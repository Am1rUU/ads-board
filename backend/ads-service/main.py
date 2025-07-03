from fastapi import FastAPI, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId

app = FastAPI()

# 🔌 Подключение к MongoDB
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.environ.get("MONGO_DB", "ads_db")

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]
ads_collection = db.ads

# 🔧 Модель ответа
class Ad(BaseModel):
    id: str
    apartment: int
    author: str
    title: str
    content: str
    student_id: str
    created_at: datetime
    hidden: bool = False


@app.get("/ads/health")
async def health():
    return {"status": "ok"}

# 🔧 GET /ads — показать только не скрытые
@app.get("/ads", response_model=List[Ad])
async def get_ads():
    cursor = ads_collection.find({"hidden": False}).sort("created_at", -1)
    ads = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        ads.append(Ad(**doc))
    return ads

# 🔧 POST /ads/create
@app.post("/ads/create")
async def create_ad(
    apartment: int = Form(...),
    author: str = Form(""),
    title: str = Form(...),
    content: str = Form(...),
    student_id: str = Form(...)
):
    ad = {
        "apartment": apartment,
        "author": author,
        "title": title,
        "content": content,
        "student_id": student_id,
        "created_at": datetime.utcnow(),
        "hidden": False
    }
    result = await ads_collection.insert_one(ad)
    return {"id": str(result.inserted_id)}

@app.on_event("startup")
async def on_startup():
    # 👇 Проставляем hidden=false, если поле отсутствует
    await ads_collection.update_many(
        {"hidden": {"$exists": False}},
        {"$set": {"hidden": False}}
    )
@app.post("/ads/{ad_id}/delete")
async def delete_ad(ad_id: str, student_id: str = Form(...)):
    result = await ads_collection.delete_one({
        "_id": ObjectId(ad_id),
        "student_id": student_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return {"message": "deleted"}

@app.post("/ads/{ad_id}/toggle_hide")
async def toggle_hide(ad_id: str, student_id: str = Form(...)):
    ad = await ads_collection.find_one({
        "_id": ObjectId(ad_id),
        "student_id": student_id
    })
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    new_hidden = not ad.get("hidden", False)
    await ads_collection.update_one(
        {"_id": ObjectId(ad_id)},
        {"$set": {"hidden": new_hidden}}
    )
    return {"message": "updated", "hidden": new_hidden}

@app.get("/ads/mine", response_model=List[Ad])
async def get_my_ads(student_id: str):
    cursor = ads_collection.find({"student_id": student_id}).sort("created_at", -1)
    ads = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        ads.append(Ad(**doc))
    return ads

