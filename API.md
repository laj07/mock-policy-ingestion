# API Reference

Base URL: `http://127.0.0.1:8000`

---

## POST /poll

Scans the mock source folders for new files, runs each through the LangGraph 
pipeline, and returns the routed results.

**Request body:** none

**Response 200:**
```json
{
  "new_files_found": 3,
  "source_breakdown": { "s3": 2, "email": 1 },
  "paused_slips": [
    {
      "thread_id": "1cab477b-32fa-412e-9e8e-75e6c9ad978a",
      "slip": {
        "insured": "Pacific Exports",
        "coverage": "marine cargo",
        "lob": "Marine",
        "region": null,
        "confidence": 0.65,
        "status": "needs_human_review",
        "filename": "slip_messy.txt"
      }
    }
  ],
  "results": [ /* one entry per new file processed */ ]
}
```

Each entry in `results` includes: `insured`, `premium`, `territory`, `coverage`, 
`broker`, `inception`, `expiry`, `source`, `filename`, `lob`, `region`, `confidence`, 
`status`, `thread_id`, `paused`.

`paused_slips` is a convenience subset — only the entries currently frozen at 
`interrupt()`, waiting on `/validate`.

---

## POST /validate/{thread_id}

Resumes a paused pipeline run with the human reviewer's decision.

**Path parameter:** `thread_id` (string, from a `/poll` response)

**Request body:**
```json
{
  "status": "approved",
  "corrected_lob": "Marine",
  "corrected_region": "Australia",
  "reviewer": "human"
}
```
(Body is a free-form dict — whatever the reviewer submits gets stored on the slip 
as `human_decision` and used to resume the graph.)

**Response 200:**
```json
{
  "message": "Decision submitted, pipeline resumed",
  "paused": false,
  "final_state": [ /* routed slip data after resuming */ ]
}
```

---

## GET /status

Returns which files have already been processed (dedup tracking).

**Response 200:**
```json
{
  "processed_files": 7,
  "files": ["slip_marine.txt", "slip_aviation.txt", "..."]
}
```

---

## GET /preview/{filename}

Returns the raw text content of a specific slip file, for debugging.

**Path parameter:** `filename`

**Response 200:**
```json
{ "filename": "slip_marine.txt", "content": "PLACING SLIP\n\nBroker: ..." }
```

**Response (not found):**
```json
{ "error": "file not found" }
```

---

## DELETE /reset

Clears `processed.json` so all slips in the mock folders will be treated as new 
on the next `/poll`. Dev/testing utility only — not intended for the reviewer-facing UI.

**Response 200:**
```json
{ "message": "processed list cleared" }
```