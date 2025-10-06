# import os
# import re
# import requests
# import pandas as pd
# import json
# import io
# import matplotlib.pyplot as plt
# import numpy as np
# from typing import Dict, List
# import google.generativeai as genai

# from utils.encoding import fig_to_data_uri_under_limit

# def extract_url(text: str) -> str | None:
#     m = re.search(r"https?://\S+", text) 
#     return m.group(0) if m else None

# def normalize_columns(df: pd.DataFrame) -> pd.DataFrame: 
#     df = df.copy()
#     df.columns = (
#         df.columns.astype(str)
#         .str.strip()
#         .str.lower()
#         .str.replace(r"\s+", "_", regex=True)
#         .str.replace(r"[^\w]", "", regex=True)
#     )
#     return df

# def alias_columns(df: pd.DataFrame, expected: list[str]) -> pd.DataFrame: 
#     for col in expected:
#         norm = col.lower()
#         if norm in df.columns and col not in df.columns:
#             df[col] = df[norm]
#     return df

# def run_chart_code(code: str, df: pd.DataFrame) -> str: 
   
#     df = normalize_columns(df)
#     referenced = re.findall(r"df\[['\"](.*?)['\"]\]", code)
#     df = alias_columns(df, referenced)

#     plt.figure()       
#     exec(code, {"plt": plt, "pd": pd, "np": np, "df": df})
#     uri = fig_to_data_uri_under_limit(fmt="png", max_bytes=100_000)
#     plt.close()
#     return uri

#   #q_text: question.txt
#   #attachment: url pr csv
  
# async def handle_generic_scraper(
#     q_text: str,
#     attachments: Dict[str, any],
#     numbered_questions: List[str],
#     wants_array: bool,
#     wants_object: bool,
#     started_ts: float,
# ):
#     url = extract_url(q_text)
#     if not url:
#         return {"error": "No URL found in questions.txt"}

#     headers = {"User-Agent": "Mozilla/5.0"}
#     resp = requests.get(url, headers=headers, timeout=20)
#     resp.raise_for_status()
#     html = resp.text

#     try:
#         tables = pd.read_html(io.StringIO(html))
#     except Exception:
#         tables = []

#     df = tables[0] if tables else pd.DataFrame()

#     extra_tables = []
#     for k, file in attachments.items():
#         if k.lower().endswith(".csv"):
#             try:
#                 df_extra = pd.read_csv(file.file)
#                 extra_tables.append(f"{k}:\n{df_extra.head(10).to_csv(index=False)}")
#             except Exception as e:
#                 print(f"Failed reading {k}: {e}")

#     table_samples = []
#     for i, tdf in enumerate(tables[:3]):
#         table_samples.append(f"HTML Table {i}:\n{tdf.head(10).to_csv(index=False)}")
#     table_samples.extend(extra_tables)

#     context = (
#         f"You are a data analyst. You are given tables scraped from {url} "
#         f"and any optional CSVs provided by the user.\n\n"
#         f"Tables (CSV sample):\n{''.join(table_samples)}\n\n"
#         f"Answer the following questions:\n"
#     )
#     context += (
#         "\nIMPORTANT:\n"
#         "- Return ONLY a JSON array.\n"
#         "- If a chart is required, return valid Python matplotlib code using 'df'.\n"
#         "- Do NOT use seaborn or other libs, only matplotlib, pandas, numpy.\n"
#         "- DO NOT return base64 directly.\n"
#     )

#     for i, q in enumerate(numbered_questions, 1):
#         context += f"{i}. {q}\n"

#     genai.configure(api_key=os.environ["GEMINI_API_KEY"])
#     model = genai.GenerativeModel("gemini-2.5-flash")
#     response = model.generate_content(context)

#     answer_text = response.text.strip()

#     if answer_text.startswith("```"):
#         answer_text = re.sub(r"^```[a-zA-Z]*\n", "", answer_text)
#         answer_text = re.sub(r"\n```$", "", answer_text)
#         answer_text = answer_text.strip()

#     try:
#         parsed = json.loads(answer_text)
#     except Exception as e:
#         print("JSON parse failed:", e)
#         return {"error": "Invalid JSON", "raw": answer_text}

#     result = []
#     for item in parsed:
#         if isinstance(item, dict):
#             new_item = {}
#             for key, val in item.items():
#                 if isinstance(val, str) and "plt." in val and "df" in val:
#                     try:
#                         uri = run_chart_code(val, df)
#                         new_item[key] = uri
#                     except Exception as e:
#                         new_item[key] = f"Error generating chart: {e}"
#                 else:
#                     new_item[key] = val
#             result.append(new_item)
#         else:
#             result.append(item)

#     return result


import os
import re
import requests
import pandas as pd
import json
import io
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List
import google.generativeai as genai

from utils.encoding import fig_to_data_uri_under_limit
from utils.duck_utils import store_dataframe, run_sql

def extract_url(text: str) -> str | None:
    m = re.search(r"https?://\S+", text) 
    return m.group(0) if m else None

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame: 
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"[^\w]", "", regex=True)
    )
    return df

def alias_columns(df: pd.DataFrame, expected: list[str]) -> pd.DataFrame: 
    for col in expected:
        norm = col.lower()
        if norm in df.columns and col not in df.columns:
            df[col] = df[norm]
    return df

def run_chart_code(code: str, df: pd.DataFrame) -> str: 
    df = normalize_columns(df)
    referenced = re.findall(r"df\[['\"](.*?)['\"]\]", code)
    df = alias_columns(df, referenced)

    # plt.figure()       
    # exec(code, {"plt": plt, "pd": pd, "np": np, "df": df})
    # uri = fig_to_data_uri_under_limit(fmt="png", max_bytes=100_000)
    # plt.close()
    # return uri

    code = code.replace("plt.show()", "")
    code = re.sub(r"plt\.savefig\(.*?\)", "", code)

    plt.figure()

    # 🔹 Debug logs
    print("Generated matplotlib code:\n", code)
    
    exec(code, {"plt": plt, "pd": pd, "np": np, "df": df})
    
    # 🔹 Check if axes has plotted data
    print("Axes has data?:", plt.gca().has_data())
    
    uri = fig_to_data_uri_under_limit(fmt="png", max_bytes=100_000)
    plt.close()
    return uri


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

    df = tables[0] if tables else pd.DataFrame()

    # Store scraped table into DuckDB
    if not df.empty:
        store_dataframe(df, "scraper_data")

    extra_tables = []
    for k, file in attachments.items():
        if k.lower().endswith(".csv"):
            try:
                df_extra = pd.read_csv(file.file)
                store_dataframe(df_extra, f"extra_{k.replace('.','_')}")
                extra_tables.append(f"{k}:\n{df_extra.head(10).to_csv(index=False)}")
            except Exception as e:
                print(f"Failed reading {k}: {e}")

    table_samples = []
    for i, tdf in enumerate(tables[:3]):
        table_samples.append(f"HTML Table {i}:\n{tdf.head(10).to_csv(index=False)}")
    table_samples.extend(extra_tables)

    context = (
        f"You are a data analyst. You are given tables scraped from {url} "
        f"and any optional CSVs provided by the user.\n\n"
        f"Tables (CSV sample):\n{''.join(table_samples)}\n\n"
        f"Answer the following questions:\n"
    )
    context += (
        "\nIMPORTANT:\n"
        "- Return ONLY a JSON array.\n"
        "- If a chart is required, return valid Python matplotlib code using 'df'.\n"
        "- If SQL is required, return SQL query referencing 'scraper_data' or 'extra_*' tables.\n"
        "- Do NOT use seaborn or other libs, only matplotlib, pandas, numpy.\n"
        "- DO NOT return base64 directly.\n"
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
    except Exception as e:
        print("JSON parse failed:", e)
        return {"error": "Invalid JSON", "raw": answer_text}

    result = []
    for item in parsed:
        if isinstance(item, dict):
            new_item = {}
            for key, val in item.items():
                if isinstance(val, str):
                    if "plt." in val and "df" in val:
                        try:
                            uri = run_chart_code(val, df)
                            new_item[key] = uri
                        except Exception as e:
                            new_item[key] = f"Error generating chart: {e}"
                    elif val.lower().startswith("select"):
                        try:
                            sql_result = run_sql(val)
                            new_item[key] = sql_result.to_dict(orient="records")
                        except Exception as e:
                            new_item[key] = f"Error executing SQL: {e}"
                    else:
                        new_item[key] = val
                else:
                    new_item[key] = val
            result.append(new_item)
        else:
            result.append(item)

    return result
