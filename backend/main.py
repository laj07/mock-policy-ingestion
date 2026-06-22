from fastapi import FastAPI
from pathlib import Path
import json

app = FastAPI()

S3_FOLDER = Path("../mock_sources/mock_s3")
EMAIL_FOLDER = Path("../mock_sources/mock_email")
PROCESSED_FILE = Path("processed.json")

def load_processed():
    if PROCESSED_FILE.exists():
        return set(json.loads(PROCESSED_FILE.read_text()))
    return set()

def save_processed(processed):
    PROCESSED_FILE.write_text(json.dumps(list(processed)))

@app.post("/poll")
def poll():
    processed = load_processed()
    new_files = []
    source_counts = {"s3": 0, "email": 0}

    for folder, source in [(S3_FOLDER, "s3"), (EMAIL_FOLDER, "email")]:
        for ext in ["*.txt", "*.eml", "*.pdf"]:
            for filepath in folder.glob(ext):
                if filepath.name not in processed:
                    content = filepath.read_text(encoding="utf-8")
                    new_files.append({
                        "source": source,
                        "filename": filepath.name,
                        "content": content
                    })
                    processed.add(filepath.name)
                    source_counts[source] += 1

    save_processed(processed)
    return {
        "new_files_found": len(new_files),
        "source_breakdown": source_counts,
        "files": new_files
    }

@app.get("/status")
def get_status():
    processed = load_processed()
    return {
        "processed_files": len(processed),
        "files": list(processed)
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
def reset():
    save_processed(set())
    return {"message": "processed list cleared"}
