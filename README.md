# Mock Policy Ingestion 

React dashboard for the mock policy ingestion pipeline.

## What it does
- Polls the FastAPI backend for new insurance slips
- Displays slips in three columns: Auto Approved, Needs Review, Rejected
- Reviewer can correct LOB and region on low-confidence slips before approving or rejecting


START → ingestion → classification → confidence
                                          ↓
                              ┌─── auto_approved ───→ END
                              ├─── needs_human_review ───→ human_review → END
                              └─── rejected ───→ reject → END

## Run
```bash
npm install
npm run dev
```

Opens at http://localhost:5173

## Backend
Make sure the FastAPI backend is running at http://127.0.0.1:8000 before polling.
