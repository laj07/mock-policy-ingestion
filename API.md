# API Reference

Base URL: `http://127.0.0.1:8000`

All endpoints marked **🔒** require header: `x-api-key: dev-secret-key`

---

## POST /poll 🔒

Scans `mock_sources/mock_s3/` (and `mock_sources/mock_email/` if it exists) for new 
files, runs each through the LangGraph pipeline, and returns the routed results. 
Skips files already seen by filename or by content hash.

**Response 200:**
```json
{
  "new_files_found": 3,
  "duplicates_skipped": 0,
  "source_breakdown": { "s3": 3, "email": 0 },
  "paused_slips": [
    {
      "thread_id": "e4f71622-af27-4c4a-9228-d76c645ea645",
      "slip": {
        "insured": "Apex Manufacturing Ltd",
        "coverage": "Commercial Property - Material Damage",
        "lob": "Property",
        "region": null,
        "confidence": 0.65,
        "filename": "slip_property.txt",
        "paused": true
      }
    }
  ],
  "results": [ /* one entry per new file processed */ ]
}
```

Each entry in `results` includes: `insured`, `premium`, `territory`, `coverage`, 
`broker`, `inception`, `expiry`, `source`, `filename`, `lob`, `region`, `confidence`, 
`status`, `thread_id`, `paused`, and `draft` (only present once a slip reaches 
`auto_approved` or `approved`).

**401** if `x-api-key` is missing or wrong.

---

## POST /validate/{thread_id} 🔒

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
`status: "approved"` routes the slip to the drafting agent. Anything else (or a 
missing `status`) routes it to rejection.

**Response 200:**
```json
{
  "message": "Decision submitted, pipeline resumed",
  "paused": false,
  "final_state": [ /* routed slip, including "draft" if approved */ ]
}
```

This works even if the backend process was restarted between `/poll` and `/validate`,
the paused state is read from `checkpoints.sqlite`, not memory.

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

**Response 200:**
```json
{ "filename": "slip_marine.txt", "content": "PLACING SLIP\n\nBroker: ..." }
```

**Response (not found):**
```json
{ "error": "file not found" }
```

---

## DELETE /reset 🔒

Clears `processed.json` (both filenames and hashes) so all slips will be treated 
as new on the next `/poll`. Dev/testing utility, not for the reviewer-facing UI.

**Response 200:**
```json
{ "message": "processed list cleared" }
```