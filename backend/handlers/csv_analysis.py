import os, re, json, io
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai
from typing import Dict, List
from utils.encoding import fig_to_data_uri_under_limit
from utils.duck_utils import store_dataframe, run_sql

async def handle_csv_analysis(
    q_text: str,
    attachments: Dict[str, any],
    numbered_questions: List[str],
    wants_array: bool,
    wants_object: bool,
    started_ts: float,
):
    key = next((k for k in attachments if k.lower().endswith(".csv")), None)
    if not key:
        return {"error": "No CSV file uploaded"}

    # Load CSV into Pandas
    df = pd.read_csv(attachments[key].file)

    # Store in DuckDB for SQL queries
    store_dataframe(df, "csv_data")

    schema = {col: str(df[col].dtype) for col in df.columns}
    sample = df.head(10).to_dict(orient="records")

    context = f"""
You are a data analyst.

Here is a CSV dataset schema:
{json.dumps(schema, indent=2)}

Here is a sample of the data:
{json.dumps(sample, indent=2)}

Answer the following questions based only on this CSV:
{q_text}

IMPORTANT:
- Return ONLY a JSON object with the requested keys.
- If a chart is required, return valid Python matplotlib code using "df".
- If SQL is required, return a SQL query referencing table "csv_data".
- DO NOT return base64 or "data:image..." strings.
- Do not include explanations or markdown.
"""
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(context)
    raw = response.text.strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n", "", raw)
        raw = re.sub(r"\n```$", "", raw)

    try:
        parsed = json.loads(raw)
    except Exception:
        return {
            "error": "LLM returned invalid JSON",
            "raw": raw,
            "fallback": {"output": raw}
        }

    result = {}
    for key, val in parsed.items():
        if isinstance(val, str):
            code = val.strip()

            # Case 1: Matplotlib chart

            if "plt." in code and "df" in code:
             try:
                 plt.figure()

                 # 🔹 Debug logs
                 print("Generated matplotlib code:\n", code)

                 exec(code, {"plt": plt, "pd": pd, "df": df})

                 # 🔹 Check if plot actually has data
                 print("Axes has data?:", plt.gca().has_data())

                 uri = fig_to_data_uri_under_limit(fmt="png", max_bytes=100_000)
                 plt.close()
                 result[key] = uri
             except Exception as e:
                 result[key] = f"Error generating chart: {e}"


            # Case 2: SQL query
            elif code.lower().startswith("select"):
                try:
                    sql_result = run_sql(code)
                    result[key] = sql_result.to_dict(orient="records")
                except Exception as e:
                    result[key] = f"Error executing SQL: {e}"

            else:
                result[key] = val
        else:
            result[key] = val

    return result
