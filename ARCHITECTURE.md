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
POST /poll
│
▼
scan mock_sources/mock_s3 + mock_email
│  (skip filenames already in processed.json)
▼
for each new file → run LangGraph pipeline (one invoke per slip)
START
│
▼
ingestion_agent        — parse raw text into 7 fields
│
▼
classification_agent   — keyword rules → LOB + region
│
▼
confidence_router      — score + decide route
│
├── confidence ≥ 0.85 ──────────────→ END  (status: auto_approved)
│
├── 0.6 ≤ confidence < 0.85 ─→ interrupt() ─→ human_review → END
│        (graph PAUSES here, waits for POST /validate/{thread_id})
│
└── confidence < 0.6 ───────────────→ reject → END  (status: rejected)
```

Each slip gets its own `thread_id` and its own graph run, so routing is independent 
per slip (this was a fix — the first version batched all slips through one shared 
state and only the first slip's status determined the route for everyone).

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

State is a dict passed between nodes. Each agent function reads what it needs, adds 
its output, and returns the updated state. LangGraph merges it and passes it to the 
next node.

## Human-in-the-loop mechanics

- `interrupt()` (from `langgraph.types`) is called inside `confidence_router` when 
  status is `needs_human_review`. This freezes graph execution at that exact point.
- A `MemorySaver` checkpointer (from `langgraph.checkpoint.memory`) stores the frozen 
  state, keyed by `thread_id`.
- `GET`-equivalent: `pipeline.get_state(config)` checks if a run is paused (`state.next` 
  is non-empty).
- To resume: `pipeline.invoke(Command(resume=decision), config=config)` LangGraph 
  looks up the paused state by `thread_id` and continues from where it left off.
- **Without the checkpointer**, `interrupt()` still pauses, but there's nothing to 
  resume from so `thread_id` becomes meaningless and `/validate` has nothing to look up.

## Gaps vs. target end-state

| Piece | Target | Current |
|---|---|---|
| Sources | Real S3 + IMAP | Local mock folders |
| Classification | Bedrock Claude Sonnet 4.6 | Keyword rules |
| Clause lookup | Vector search (Titan Embeddings) over 500+ clauses | Not built |
| Drafting agent | Claude renders final policy wording | Not built |
| Checkpointer | Postgres/DynamoDB | In-memory (MemorySaver) |
| Auth | Presumably required for production | None |
| Duplicate detection | Explicit duplicate registry | Only filename-based (`processed.json`) |