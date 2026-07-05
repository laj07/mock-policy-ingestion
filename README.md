# Mock Policy Ingestion

A prototype automating the manual policy drafting workflow run by a policy admin team. 
Broker slips arrive by email or land on a shared drive/S3. The system extracts fields, 
classifies the policy type and region, scores confidence, and routes low-confidence slips 
to a human reviewer via a React dashboard before drafting.

Built with **FastAPI + LangGraph** on the backend and **React (Vite)** on the frontend.
Classification is currently rule-based (keyword matching) as a placeholder, the plan is 
to replace this with an AWS Bedrock (Claude Sonnet 4.6) call.

## Business Context

The policy admin team at Allianz manually reviewed every incoming broker slip, including
extracting fields, classifying policy type and territory, and triaging for review. 
This pipeline automates that workflow end to end, routing only low-confidence cases 
to human review and eliminating manual processing for high-confidence slips.

## Tech stack

- **Backend:** FastAPI, LangGraph, Python
- **Frontend:** React, Vite
- **State persistence:** LangGraph `SqliteSaver` checkpointer (file-based, survives restarts)
- **Frontend persistence:** browser `localStorage`
- **Auth:** static API key header (dev placeholder, not production-grade)

## Project Structure 
```
mock-policy-ingestion/
├── backend/
│   ├── main.py            # FastAPI app, endpoints, auth, duplicate detection
│   ├── agents.py           # ingestion, classification, confidence, drafting, reject agents
│   ├── graph.py             # LangGraph state + node/edge wiring
│   ├── processed.json       # tracks ingested filenames + content hashes (dedup)
│   └── checkpoints.sqlite    # LangGraph paused-run state, survives restarts
├── frontend/
│   └── src/App.jsx          # dashboard UI
├── mock_sources/
│   ├── mock_s3/               # simulated S3 bucket (drop .txt files here)
│   └── mock_email/            # simulated email inbox (not yet populated)
└── README.md
```

## Setup

### Backend

```bash
cd mock-policy-ingestion
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn langgraph langgraph-checkpoint-sqlite
cd backend
uvicorn main:app --reload
```

Runs at `http://127.0.0.1:8000`. Swagger docs at `http://127.0.0.1:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173`.

Both need to be running simultaneously, in separate terminals.

## Auth

`/poll`, `/validate/{thread_id}`, and `/reset` require a header:
x-api-key: dev-secret-key

This is a hardcoded dev placeholder. `/status` and `/preview/{filename}` 
are unauthenticated (read-only debug endpoints).

## Usage

1. Drop sample slip `.txt` files into `mock_sources/mock_s3/`
2. Open the dashboard, click **Poll Sources**
3. Slips are scored and sorted into three columns: **Auto Approved**, **Needs Review**, **Rejected**
4. For slips needing review, correct the LOB/region and click **Approve** or **Reject**
5. Approved slips (auto or human-reviewed) get a placeholder policy draft attached
6. Dashboard state persists across page refresh (stored in `localStorage`); paused reviews 
   persist across backend restarts (stored in `checkpoints.sqlite`)

## Known limitations (prototype stage)

- Sources are mocked local folders, not real S3/IMAP
- Only `mock_sources/mock_s3/` is populated, the email path exists in code but has no folder yet
- Classification is keyword-based, not Claude/Bedrock-based yet
- Auth is a single hardcoded key, not real user identity or key rotation
- Duplicate detection is filename + content-hash based, not a proper duplicate registry
- No clause lookup agent, drafting output is a placeholder template, not clause-merged final wording
