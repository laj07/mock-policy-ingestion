# Mock Policy Ingestion

A prototype automating the manual policy drafting workflow run by a policy admin team. 
Broker slips arrive by email or land on a shared drive/S3. The system extracts fields, 
classifies the policy type and region, scores confidence, and routes low-confidence slips 
to a human reviewer via a React dashboard before drafting.

Built with **FastAPI + LangGraph** on the backend and **React (Vite)** on the frontend.
Classification is currently rule-based (keyword matching) as a placeholder, the plan is 
to replace this with an AWS Bedrock (Claude Sonnet 4.6) call.

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

## Tech stack

- **Backend:** FastAPI, LangGraph, Python
- **Frontend:** React, Vite
- **State persistence:** LangGraph `MemorySaver` checkpointer (in-memory, dev only)
- **Frontend persistence:** browser `localStorage`

## Setup

### Backend

```bash
cd mock-policy-ingestion
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn langgraph
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

## Usage

1. Drop sample slip `.txt` files into `mock_sources/mock_s3/` or `mock_sources/mock_email/`
2. Open the dashboard, click **Poll Sources**
3. Slips are scored and sorted into three columns: **Auto Approved**, **Needs Review**, **Rejected**
4. For slips needing review, correct the LOB/region and click **Approve** or **Reject**
5. Dashboard state persists across page refresh (stored in `localStorage`)

## Known limitations (prototype stage)

- Sources are mocked local folders, not real S3/IMAP
- Classification is keyword-based, not Claude/Bedrock-based yet
- No authentication on any endpoint
- Checkpointer is in-memory, so paused review states are lost on backend restart
- No drafting agent yet, pipeline stops after human validation
