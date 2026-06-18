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

    for folder, source in [(S3_FOLDER, "s3"), (EMAIL_FOLDER, "email")]:
        for filepath in folder.glob("*.*"):
            if filepath.name not in processed:
                content = filepath.read_text(encoding="utf-8")
                new_files.append({
                    "source": source,
                    "filename": filepath.name,
                    "content": content
                })
                processed.add(filepath.name)

    save_processed(processed)
    return {"new_files_found": len(new_files), "files": new_files}