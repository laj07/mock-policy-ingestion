## What it does
Polls two local folders (mock S3 and mock email) for new insurance slip files.
Tracks processed files so no duplicates are picked up twice.

## Run
cd backend
uvicorn main:app --reload 

----

Hit POST /poll at http://127.0.0.1:8000/docs
