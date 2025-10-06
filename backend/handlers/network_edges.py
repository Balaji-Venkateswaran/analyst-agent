import io
from typing import Dict, List

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from typing import Dict, List


from utils.encoding import fig_to_data_uri_under_limit

def _load_edges_from_attachment(attachments: Dict[str, any]) -> pd.DataFrame:
    key = None
    for k in attachments.keys():
        if k.lower().endswith("edges.csv"):
            key = k
            break
    if not key:
        raise ValueError("edges.csv not found in uploaded files")

    raw = io.BytesIO()
    raw.write(attachments[key].file.read())
    raw.seek(0)
    df = pd.read_csv(raw)

    cols = [c.lower() for c in df.columns]
    if "source" in cols and "target" in cols:
        return df.rename(columns={
            df.columns[cols.index("source")]: "source",
            df.columns[cols.index("target")]: "target"
        })
    elif len(df.columns) >= 2:
        c0, c1 = df.columns[:2]
        return df.rename(columns={c0: "source", c1: "target"})
    else:
        raise ValueError("edges.csv must have at least two columns")


def _draw_network_b64(G: nx.Graph) -> str:
    plt.figure(figsize=(6, 4), dpi=110)
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx_nodes(G, pos)
    nx.draw_networkx_edges(G, pos)
    nx.draw_networkx_labels(G, pos, font_size=8)
    plt.axis("off")
    uri = fig_to_data_uri_under_limit(fmt="png", max_bytes=100_000)
    plt.close()
    return uri


def _draw_degree_hist_b64(G: nx.Graph) -> str:
    deg = [d for _, d in G.degree()]
    vals, counts = np.unique(deg, return_counts=True)
    plt.figure(figsize=(6, 4), dpi=110)
    plt.bar(vals, counts, color="green")
    plt.xlabel("Degree")
    plt.ylabel("Count")
    plt.title("Degree Distribution")
    uri = fig_to_data_uri_under_limit(fmt="png", max_bytes=100_000)
    plt.close()
    return uri


async def handle_network_edges_task(
    q_text: str,
    attachments: Dict[str, any],
    numbered_questions: List[str],
    wants_array: bool,
    wants_object: bool,
    started_ts: float,
):
    df = _load_edges_from_attachment(attachments)
    G = nx.from_pandas_edgelist(df, "source", "target", create_using=nx.Graph)

    edge_count = G.number_of_edges()
    if G.number_of_nodes() > 0:
        node, _ = max(G.degree, key=lambda x: x[1])
        highest_degree_node = str(node)
    else:
        highest_degree_node = ""
    average_degree = (2 * edge_count / G.number_of_nodes()) if G.number_of_nodes() else 0.0
    density = nx.density(G)

    network_graph = _draw_network_b64(G)
    degree_histogram = _draw_degree_hist_b64(G)

    result_obj = {
        "edge_count": edge_count,
        "highest_degree_node": highest_degree_node,
        "average_degree": float(average_degree),
        "density": float(density),
        # "shortest_path_alice_eve": shortest_alice_eve if shortest_alice_eve is not None else -1,
        "network_graph": network_graph,
        "degree_histogram": degree_histogram,
    }

    if wants_object or "Return a JSON object with keys" in q_text:
        return result_obj