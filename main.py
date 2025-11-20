import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Entry

app = FastAPI(title="FinTrack API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "FinTrack Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# API models
class EntryCreate(BaseModel):
    amount: float
    currency: str = "USD"
    screenshot_url: Optional[str] = None
    note: Optional[str] = None
    category: Optional[str] = None
    occurred_at: Optional[datetime] = None

@app.post("/api/entries")
def create_entry(payload: EntryCreate):
    try:
        entry = Entry(**payload.model_dump())
        inserted_id = create_document("entry", entry)
        return {"id": inserted_id, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/entries")
def list_entries(limit: int = 100):
    try:
        docs = get_documents("entry", limit=limit)
        # Convert ObjectId and datetimes to strings
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
            for k, v in list(d.items()):
                if isinstance(v, datetime):
                    d[k] = v.isoformat()
        return {"items": docs, "count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
