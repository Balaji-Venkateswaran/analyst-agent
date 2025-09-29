
# import os, re, json
# import pandas as pd
# import matplotlib.pyplot as plt
# import google.generativeai as genai
# from typing import Dict, List
# from utils.encoding import fig_to_data_uri_under_limit

# async def handle_csv_analysis(
#     q_text: str,
#     attachments: Dict[str, any],
#     numbered_questions: List[str],
#     wants_array: bool,
#     wants_object: bool,
#     started_ts: float,
# ):
#     # 1. Locate CSV file
#     key = next((k for k in attachments.keys() if k.lower().endswith(".csv")), None)
#     if not key:
#         return {"error": "No CSV file uploaded"}
#     df = pd.read_csv(attachments[key].file)

#     # 2. Build schema + sample
#     schema = {col: str(df[col].dtype) for col in df.columns}
#     sample = df.head(10).to_dict(orient="records")

#     # 3. Prompt Gemini
#     context = f"""
# You are a data analyst.

# Dataset schema:
# {json.dumps(schema, indent=2)}

# Sample rows:
# {json.dumps(sample, indent=2)}

# Answer the following questions based only on this CSV:
# {q_text}

# IMPORTANT:
# - Return ONLY a JSON object with the keys requested.
# - If a chart is requested, provide a Python matplotlib code string using df.
# - Do not include explanations or markdown.
# """

#     genai.configure(api_key=os.environ["GEMINI_API_KEY"])
#     model = genai.GenerativeModel("gemini-2.5-flash")
#     response = model.generate_content(context)
#     raw = response.text.strip()

#     if raw.startswith("```"):
#         raw = re.sub(r"^```[a-zA-Z]*\n", "", raw)
#         raw = re.sub(r"\n```$", "", raw)

#     try:
#         parsed = json.loads(raw)
#     except Exception:
#         return {"error": "LLM returned invalid JSON", "raw": raw}

#     # 4. Execute matplotlib code if provided
#     result = {}
#     for key, val in parsed.items():
#         if isinstance(val, str) and val.strip().startswith("plt."):
#             try:
#                 plt.figure()
#                 exec(val, {"plt": plt, "pd": pd, "df": df})
#                 uri = fig_to_data_uri_under_limit(fmt="png", max_bytes=100_000)
#                 plt.close()
#                 result[key] = uri
#             except Exception as e:
#                 result[key] = f"Error generating chart: {e}"
#         else:
#             result[key] = val

#     return result


import os, re, json, io
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai
from typing import Dict, List
from utils.encoding import fig_to_data_uri_under_limit

async def handle_csv_analysis(
    q_text: str,
    attachments: Dict[str, any],
    numbered_questions: List[str],
    wants_array: bool,
    wants_object: bool,
    started_ts: float,
):
    # 1. Load first CSV
    key = next((k for k in attachments if k.lower().endswith(".csv")), None)
    if not key:
        return {"error": "No CSV file uploaded"}
    df = pd.read_csv(attachments[key].file)

    # 2. Schema + sample
    schema = {col: str(df[col].dtype) for col in df.columns}
    sample = df.head(10).to_dict(orient="records")

    # 3. Prompt Gemini
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
- If a chart is required, return valid Python matplotlib code using "df" (already loaded as a pandas DataFrame).
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
        # return {"error": "LLM returned invalid JSON", "raw": raw}
         return {
        "error": "LLM returned invalid JSON",
        "raw": raw,
        "fallback": {"output": raw}  # ensure it's valid JSON structure
    }

    # 4. Execute matplotlib code if present
    result = {}
    for key, val in parsed.items():
        if isinstance(val, str) and val.strip().startswith("plt."):
            try:
                plt.figure()
                exec(val, {"plt": plt, "pd": pd, "df": df})
                uri = fig_to_data_uri_under_limit(fmt="png", max_bytes=100_000)
                plt.close()
                result[key] = uri
            except Exception as e:
                result[key] = f"Error generating chart: {e}"
        else:
            result[key] = val

    return result
