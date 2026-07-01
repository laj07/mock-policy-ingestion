import hashlib
import json
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command

from graph import pipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

S3_FOLDER = Path("../mock_sources/mock_s3")
EMAIL_FOLDER = Path("../mock_sources/mock_email")
PROCESSED_FILE = Path("processed.json")

API_KEY = "dev-secret-key"


def require_api_key(x_api_key: str | None = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")


def load_processed():
    if PROCESSED_FILE.exists():
        data = json.loads(PROCESSED_FILE.read_text())
        if isinstance(data, list):
            return {"filenames": set(data), "hashes": set()}
        return {"filenames": set(data.get("filenames", [])), "hashes": set(data.get("hashes", []))}
    return {"filenames": set(), "hashes": set()}


def save_processed(processed):
    PROCESSED_FILE.write_text(json.dumps({
        "filenames": list(processed["filenames"]),
        "hashes": list(processed["hashes"]),
    }))


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@app.post("/poll")
def poll(auth=Depends(require_api_key)):
    processed = load_processed()
    new_files = []
    source_counts = {"s3": 0, "email": 0}
    duplicate_count = 0

    for folder, source in [(S3_FOLDER, "s3"), (EMAIL_FOLDER, "email")]:
        if not folder.exists():
            continue
        for ext in ["*.txt", "*.eml", "*.pdf"]:
            for filepath in folder.glob(ext):
                if filepath.name in processed["filenames"]:
                    continue

                content = filepath.read_text(encoding="utf-8")
                chash = content_hash(content)

                if chash in processed["hashes"]:
                    processed["filenames"].add(filepath.name)
                    duplicate_count += 1
                    continue

                new_files.append({
                    "source": source,
                    "filename": filepath.name,
                    "content": content
                })
                processed["filenames"].add(filepath.name)
                processed["hashes"].add(chash)
                source_counts[source] += 1

    save_processed(processed)

    all_results = []
    paused_slips = []

    for file in new_files:
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        result = pipeline.invoke({"new_files": [file], "current_slip": file}, config=config)

        state = pipeline.get_state(config)
        paused = bool(state.next)

        slip_result = result.get("routed", [{}])
        if not slip_result or slip_result == [{}]:
            slip_result = result.get("extracted", [{}])
        slip_result = slip_result[0] if slip_result else {}
        slip_result["thread_id"] = thread_id
        slip_result["paused"] = paused

        if paused:
            paused_slips.append({"thread_id": thread_id, "slip": slip_result})

        all_results.append(slip_result)

    return {
        "new_files_found": len(new_files),
        "duplicates_skipped": duplicate_count,
        "source_breakdown": source_counts,
        "paused_slips": paused_slips,
        "results": all_results
    }


@app.post("/validate/{thread_id}")
def validate(thread_id: str, decision: dict, auth=Depends(require_api_key)):
    config = {"configurable": {"thread_id": thread_id}}
    pipeline.invoke(Command(resume=decision), config=config)
    final_state = pipeline.get_state(config)
    return {
        "message": "Decision submitted, pipeline resumed",
        "paused": bool(final_state.next),
        "final_state": final_state.values.get("routed", [])
    }


@app.get("/status")
def get_status():
    processed = load_processed()
    return {
        "processed_files": len(processed["filenames"]),
        "files": list(processed["filenames"])
    }


@app.get("/preview/{filename}")
def preview(filename: str):
    for folder in [S3_FOLDER, EMAIL_FOLDER]:
        filepath = folder / filename
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            return {"filename": filename, "content": content}
    return {"error": "file not found"}


@app.delete("/reset")
def reset(auth=Depends(require_api_key)):
    save_processed({"filenames": set(), "hashes": set()})
    return {"message": "processed list cleared"}