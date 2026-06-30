# Mock Policy Ingestion

A React-based dashboard for a mock insurance policy ingestion pipeline powered by a FastAPI + LangGraph backend. The application visualizes the status of incoming insurance slips and enables human review for low-confidence classifications.

## What it does

- Polls the FastAPI backend for new insurance slips
- Routes each slip through a LangGraph pipeline (ingestion → classification → confidence routing)
- Displays slips in three columns: Auto Approved, Needs Review, Rejected
- Reviewer can correct LOB and region on low-confidence slips before approving or rejecting

## Pipeline flow
```
START → ingestion → classification → confidence
                                          ↓
                              ┌─── auto_approved ───→ END
                              ├─── needs_human_review ───→ human_review → END
                              └─── rejected ───→ reject → END
```
## Tech stack

React, Vite, FastAPI, LangGraph

## Run

**Backend** (from `/backend`):
```bash
uvicorn main:app --reload
```

**Frontend** (from `/frontend`):
```bash
npm install
npm run dev
```

Frontend opens at http://localhost:5173, backend runs at http://127.0.0.1:8000
