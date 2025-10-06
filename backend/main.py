import sys, os
import re, time
from typing import Dict, List

import google.generativeai as genai
from dotenv import load_dotenv

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from handlers.generic_scraper import handle_generic_scraper
# from handlers.network_edges import handle_network_edges_task
from handlers.csv_analysis import handle_csv_analysis
sys.path.append(os.path.dirname(__file__))


app = FastAPI(title="Data Analyst Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["https://analyst-agent-iernvbm0y-balajis-projects-613078f7.vercel.app/"],
    # allow_origins=["*"],
    allow_origins=[
        "https://analyst-agent-iernvbm0y-balajis-projects-613078f7.vercel.app",  # your Vercel frontend
        "https://analyst-agent-frontend.onrender.com",  # if hosted on Render
        "http://localhost:8000",  # for local testing
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv(override=True)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file!")

# print("Loaded GEMINI_API_KEY:", api_key[:10] + "*****")

genai.configure(api_key=api_key)

MODEL = genai.GenerativeModel("gemini-2.5-flash")

RECOGNIZERS = [
    (lambda q, attachments: "http" in q.lower(), handle_generic_scraper),
    (lambda q, attachments: any(fname.lower().endswith(".csv") for fname in attachments.keys()),
     handle_csv_analysis),
]

def split_questions(text: str) -> List[str]:
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if re.match(r"^(\d+[\).\]]\s+|-\s+|\*\s+)", s):
            s = re.sub(r"^(\d+[\).\]]\s+|-\s+|\*\s+)", "", s).strip()
            lines.append(s)
    return lines or [text.strip()]

@app.post("/api/")
async def analyze(files: List[UploadFile] = File(...)):
    started = time.time()

    questions_file: UploadFile | None = None
    attachments: Dict[str, UploadFile] = {}
    for f in files:
        if f.filename.lower().endswith("questions.txt"):
            questions_file = f
        else:
            attachments[f.filename] = f

    if not questions_file:
        raise HTTPException(status_code=400, detail="questions.txt is required in the form-data")

    try:
        q_text = (await questions_file.read()).decode("utf-8", errors="ignore")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed reading questions.txt: {e}")

    wants_array = bool(re.search(r"respond with a json array", q_text, re.I))
    wants_object = bool(re.search(r"return a json object", q_text, re.I))
    numbered_questions = split_questions(q_text)

    for predicate, handler in RECOGNIZERS:
        if predicate(q_text, attachments):
           result = await handler(q_text, attachments, numbered_questions, wants_array, wants_object, started)
           return result


    return {
        "status": "unrecognized_task",
        "message": "The question format was not recognized by built-in handlers.",
        "questions_detected": numbered_questions,
        "received_files": list(attachments.keys()),
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
