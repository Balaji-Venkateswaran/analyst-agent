# Data Analyst Agent API (Python 3.13.7)

A FastAPI service that accepts `questions.txt` and optional attachments (e.g., CSVs) and returns answers (including base64 plots). No Docker needed.

## Quick Start

1) **Create venv & install deps**
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows
# or: source .venv/bin/activate (macOS/Linux)
pip install -r requirements.txt
