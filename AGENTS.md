# Agents

Five functions total, four registered as LangGraph nodes plus the routing logic 
embedded in `confidence_router`. Each takes the shared state dict, does one job, 
and returns the updated state.

## 1. ingestion_agent

**Input:** `state["current_slip"]`, raw text + metadata for one file
**Output:** `state["extracted"]`, dict of 7 fields

Extracts: `insured`, `premium`, `territory`, `coverage`, `broker`, `inception`, `expiry`.

Two-pass approach:
1. **Structured pass**, splits each line on `:`, matches known keys (`insured`, 
   `broker`, `coverage`/`type`, `territory`/`territory/location`, `period` which is 
   split on "to" into inception + expiry, etc).
2. **Fallback pass**, for any field still `null`, scans the raw text word-by-word 
   for keyword hints and grabs the words immediately following, stopping at common 
   stop-words.

Known gap: fails on genuinely unlabelled/jumbled text, which is what Bedrock 
classification is meant to close.

## 2. classification_agent

**Input:** `state["extracted"]`
**Output:** `state["classified"]`, adds `lob` and `region`

Pure keyword matching, no model call yet. Slated to be replaced with a Bedrock 
Claude Sonnet 4.6 call.

## 3. confidence_router

**Input:** `state["classified"]`
**Output:** `state["routed"]`, `state["route"]`

Scoring:
- LOB found and region found → confidence `0.9`
- Only one found → confidence `0.65`
- Neither found → confidence `0.25`

Routing:
- `≥ 0.85` → `status: auto_approved`
- `0.6 to 0.84` → calls `interrupt()`, freezing the graph. **On resume**, reads the 
  human's decision: `status == "approved"` sets `status: approved` and applies any 
  `corrected_lob`/`corrected_region`; anything else sets `status: rejected`. The 
  function does not return until this is resolved, so `route` is always a terminal 
  value (`auto_approved`, `approved`, or `rejected`), never left at 
  `needs_human_review`.
- `< 0.6` → `status: rejected`

This is also where the pause/resume for human review actually lives, there's no 
separate "human review" node in the graph. Slips are processed one at a time so 
routing is accurate per-slip.

## 4. drafting_agent

**Input:** `state["routed"]` (a slip with `status` of `auto_approved` or `approved`)
**Output:** adds a `draft` field, a formatted placeholder policy text

Runs after any approval path (automatic or human-approved). Currently just 
templates the extracted fields into a plain-text draft. Real version will merge 
matched clause library wording, finalized by Claude, once the lookup agent exists.

## 5. reject_agent

**Input:** `state["routed"]` (a slip with `status: rejected`)
**Output:** unchanged state, logs the filename

Runs for both auto-rejected (confidence < 0.6) and human-rejected slips.

## Not yet built

- **Lookup agent**, semantic search over the clause library (Titan Embeddings), 
  duplicate check by content similarity rather than exact hash
- **Real drafting**, clause-merged, Claude-finalized wording instead of the 
  placeholder template