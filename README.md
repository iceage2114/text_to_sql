# Text-to-SQL Agent

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`:

```env
GITHUB_TOKEN=ghp_your_token_here
MSSQL_CONN_STR=DRIVER={ODBC Driver 17 for SQL Server};SERVER=JONATHANS-PC\SQLEXPRESS;DATABASE=AdventureWorks2019;Trusted_Connection=yes
```

## Run

**Terminal 1 — API:**
```powershell
uvicorn api.main:app --reload --port 8080
```

**Terminal 2 — UI:**
```powershell
streamlit run ui/app.py
```

UI: `http://localhost:8501` · API docs: `http://127.0.0.1:8080/docs`

## First-time schema ingestion

Click **📥 Ingest / Refresh Schema** in the sidebar, or:

```powershell
python -m schema.ingestion
```
