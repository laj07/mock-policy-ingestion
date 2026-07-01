# Architecture

## Target end-state (per original spec)

```
Email (IMAP) ─┐
S3 / Drive ────┼──→ Ingestion Agent → Classification Agent → Clause Lookup Agent
Portal upload ┘        (extract)         (LOB + region,        (semantic search,
Claude/Bedrock)       500+ clause library,
duplicate check)
│
▼
Human Validation (React UI)
│
▼
Drafting Agent
(merge corrections + clauses,
render template, Claude
finalizes wording)
```

All model calls (extraction, classification, clause matching, drafting) go through 
**AWS Bedrock — Claude Sonnet 4.6**. Titan Embeddings used for the clause vector store.

## Current implementation (this prototype)

```
POST /poll   (requires x-api-key)
│
▼
scan mock_sources/mock_s3   (mock_email path exists, folder not yet populated)
│  skip if filename already seen, OR content hash already seen
▼
for each new file → run LangGraph pipeline (one invoke per slip, own thread_id)
START
│
▼
ingestion_agent        (parse raw text into 7 fields)
│
▼
classification_agent   (keyword rules → LOB + region)
│
▼
confidence_router      (score, decide route, resolve human decision if paused)
│
├── confidence ≥ 0.85 ────────────────────→ drafting_agent → END
│        (status: auto_approved)
│
├── 0.6 ≤ confidence < 0.85 ─→ interrupt() ─→ [waits for POST /validate]
│        On resume:
│          decision.status == "approved" → status: approved  → drafting_agent → END
│          otherwise                       → status: rejected → reject_agent  → END
│
└── confidence < 0.6 ─────────────────────→ reject_agent → END
(status: rejected)
```

Each slip gets its own `thread_id` and its own graph run, so routing is independent 
per slip. The pause-and-resolve for human review happens **inside** `confidence_router` 
itself via `interrupt()`, there is no separate `human_review` node. By the time the 
function returns (whether on first pass or after `/validate` resumes it), `route` is 
already one of `auto_approved`, `approved`, or `rejected`, never left sitting at 
`needs_human_review`.

## State shape

```python
class SlipState(TypedDict):
    new_files: List[dict]
    extracted: List[dict]
    classified: List[dict]
    routed: List[dict]
    route: str
    current_slip: dict
```

## Human-in-the-loop mechanics

- `interrupt()` (from `langgraph.types`) is called inside `confidence_router` when 
  confidence lands in the review band. This freezes graph execution at that exact point.
- A `SqliteSaver` checkpointer (from `langgraph.checkpoint.sqlite`, file `checkpoints.sqlite`) 
  stores the frozen state, keyed by `thread_id`. **This is file-based, not in-memory**, 
  a paused run survives the backend process restarting, verified by killing and 
  restarting uvicorn mid-review and successfully resuming.
- `pipeline.get_state(config)` checks if a run is paused (`state.next` is non-empty).
- To resume: `pipeline.invoke(Command(resume=decision), config=config)`, LangGraph 
  looks up the paused state by `thread_id`, re-enters `confidence_router` right after 
  the `interrupt()` call, and finishes resolving `status` based on `decision`.

## Auth

`require_api_key` is a FastAPI dependency checking an `x-api-key` header against a 
hardcoded constant. Applied to `/poll`, `/validate`, `/reset`. Not applied to 
`/status`, `/preview` (read-only debug). This is a placeholder, production would use 
a secrets-manager-issued key or OAuth2/JWT with real user identity.

## Duplicate detection

`processed.json` now stores two sets: `filenames` and `hashes` (SHA-256 of file content). 
A file is skipped if either its filename or its content hash has been seen before, 
catching the case of the same slip re-uploaded under a different filename.

## Gaps vs. target end-state

| Piece | Target | Current |
|---|---|---|
| Sources | Real S3 + IMAP | Local mock folder (S3 only, email path unpopulated) |
| Classification | Bedrock Claude Sonnet 4.6 | Keyword rules |
| Clause lookup | Vector search (Titan Embeddings) over 500+ clauses | Not built |
| Drafting agent | Claude renders final policy wording | Placeholder template, no clause merge |
| Checkpointer | Postgres/DynamoDB | SqliteSaver (file-based, single-process) |
| Auth | Real user identity / key rotation | Single static dev key |
| Duplicate detection | Explicit duplicate registry | Filename + content hash |