import os
import re
import requests
import pandas as pd
import json
from typing import Dict, List
import google.generativeai as genai
import io

from utils.plots import scatter_with_regression

def extract_url(text: str) -> str | None:
    m = re.search(r"https?://\S+", text)
    return m.group(0) if m else None

async def handle_generic_scraper(
    q_text: str,
    attachments: Dict[str, any],
    numbered_questions: List[str],
    wants_array: bool,
    wants_object: bool,
    started_ts: float,
):

    url = extract_url(q_text)
    if not url:
        return {"error": "No URL found in questions.txt"}

    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    html = resp.text

    try:
        tables = pd.read_html(io.StringIO(html))

    except Exception:
        tables = []

    extra_tables = []
    for k, file in attachments.items():
        if k.lower().endswith(".csv"):
            try:
                df = pd.read_csv(file.file)
                extra_tables.append(f"{k}:\n{df.head(10).to_csv(index=False)}")
            except Exception as e:
                print(f"Failed reading {k}: {e}")

    table_samples = []
    for i, df in enumerate(tables[:3]):
        table_samples.append(f"HTML Table {i}:\n{df.head(10).to_csv(index=False)}")
    table_samples.extend(extra_tables)

    context = (
        f"You are a data analyst. You are given tables scraped from {url} "
        f"and any optional CSVs provided by the user.\n\n"
        f"Tables (CSV sample):\n{''.join(table_samples)}\n\n"
        f"Answer the following questions:\n"
    )
    context += (
        "\nIMPORTANT:\n"
        "Return ONLY a JSON array of answers, no explanations, no markdown fences.\n"
        "Correct format example:\n"
        # "[1, \"xxx\", 0.48, \"data:image/png;base64,...\"]\n"
    )

    for i, q in enumerate(numbered_questions, 1):
        context += f"{i}. {q}\n"

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(context)

    answer_text = response.text.strip()

    if answer_text.startswith("```"):
        answer_text = re.sub(r"^```[a-zA-Z]*\n", "", answer_text)
        answer_text = re.sub(r"\n```$", "", answer_text)
        answer_text = answer_text.strip()

    try:
        parsed = json.loads(answer_text)
        if isinstance(parsed, list):
            return parsed
    except Exception as e:
        print("JSON parse failed, raw text returned:", e)

    return [answer_text]
