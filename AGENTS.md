# Agents

Four functions registered as LangGraph nodes. Each takes the shared state dict, 
does one job, and returns the updated state. Slips currently only arrive from 
`mock_sources/mock_s3/`, the email path exists in `main.py` but has no folder to 
read from yet.

## 1. ingestion_agent

**Input:** `state["current_slip"]`, raw text + metadata for one file
**Output:** `state["extracted"]`, dict of 7 fields

Extracts: `insured`, `premium`, `territory`, `coverage`, `broker`, `inception`, `expiry`.

Two-pass approach:
1. **Structured pass**, splits each line on `:`, matches known keys (`insured`, 
   `broker`, `coverage`/`type`, `territory`/`territory/location`, `period` which is 
   split on "to" into inception + expiry, etc).
2. **Fallback pass**, for any field still `null`, scans the raw text word-by-word 
   for keyword hints (e.g. "insured", "client", "policyholder" all map to the 
   `insured` field) and grabs the words immediately following, stopping at common 
   stop-words.

This handles both clean `Key: Value` slips and looser sentence-based slips, though 
it still fails on genuinely unlabelled/jumbled text, that's the known gap Bedrock 
classification is meant to close.

## 2. classification_agent

**Input:** `state["extracted"]`
**Output:** `state["classified"]`, adds `lob` and `region`

Pure keyword matching, no model call yet:
- `coverage` contains "marine cargo" → Marine; "aviation" → Aviation; "property" → Property
- `territory` contains "uk"/"united kingdom"/"ireland" → UK; "australia" → Australia; 
  "usa"/"united states" → USA

This is the piece slated to be replaced with a Bedrock Claude Sonnet 4.6 call, so it 
can classify unstructured/abbreviated text by context rather than exact keyword match.

## 3. confidence_router

**Input:** `state["classified"]`
**Output:** `state["routed"]`, `state["route"]`, and (conditionally) triggers `interrupt()`

Scoring:
- LOB found and region found → confidence `0.9`
- Only one found → confidence `0.65`
- Neither found → confidence `0.25`

Routing:
- `≥ 0.85` → `auto_approved`
- `0.6 to 0.84` → `needs_human_review`, calls `interrupt()`, freezing the graph and 
  surfacing the slip to the reviewer
- `< 0.6` → `rejected`

`state["route"]` is what the graph's conditional edge reads to decide which node 
runs next. Slips are processed one at a time through the graph specifically so this 
routing is accurate per-slip.

## 4. human_review_agent / reject_agent

Currently placeholder nodes, each just logs the slip filename. They exist as 
explicit graph nodes (rather than folding that logic into `confidence_router`) so 
the graph has real branching, and so each can later be expanded, e.g. `reject_agent` 
writing to an audit log, `human_review_agent` triggering a notification.

## Not yet built

- **Lookup agent**, semantic search over the clause library (Titan Embeddings), 
  duplicate check
- **Drafting agent**, merges human corrections + matched clauses into the policy 
  template, Claude finalizes wording