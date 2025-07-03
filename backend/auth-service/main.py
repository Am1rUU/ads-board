from fastapi import FastAPI, Form, HTTPException
import json
from pathlib import Path

app = FastAPI()
DB_PATH = Path(__file__).parent / "data/student_db.json"

with open(DB_PATH) as f:
    VALID_IDS = set(json.load(f)["valid_students"])

@app.get("/auth/health")
async def health():
    return {"status": "ok"}


@app.post("/login")
async def login(student_id: str = Form(...)):
    if student_id not in VALID_IDS:
        raise HTTPException(status_code=401, detail="Такого студента нет")
    return {"student_id": student_id}

