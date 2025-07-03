from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
import asyncio


templates = Jinja2Templates(directory="templates")
app = FastAPI()

AUTH_URL = "http://auth-service:8000"
ADS_URL = "http://ads-service:8000"

@app.on_event("startup")
async def wait_for_services():
    print("⏳ Ждём 5 секунд для старта сети Docker...")
    await asyncio.sleep(5)  # 🕒 Подождать перед началом пингов

    for _ in range(10):
        try:
            async with httpx.AsyncClient() as client:
                r1 = await client.get("http://auth-service:8000/auth/health")
                r2 = await client.get("http://ads-service:8000/ads/health")
                if r1.status_code == 200 and r2.status_code == 200:
                    print("✅ Все сервисы готовы")
                    return
        except Exception as e:
            print(f"⏳ Ожидание сервисов: {e}")
        await asyncio.sleep(2)
    raise RuntimeError("❌ Не удалось дождаться сервисов")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, 
"error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_action(request: Request, student_id: str = Form(...)):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{AUTH_URL}/login", 
data={"student_id": student_id})
    if response.status_code != 200:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Такого студента нет"
        })
    return RedirectResponse(url=f"/ads?student_id={student_id}", 
status_code=302)

@app.get("/ads", response_class=HTMLResponse)
async def show_ads(request: Request, student_id: str):
    async with httpx.AsyncClient() as client:
        ads_response = await client.get(f"{ADS_URL}/ads")
    ads = ads_response.json()
    return templates.TemplateResponse("ads.html", {
        "request": request,
        "ads": ads,
        "student_id": student_id
    })


@app.get("/ads/create", response_class=HTMLResponse)
async def create_ad_form(request: Request, student_id: str):
    return templates.TemplateResponse("create_ad.html", {
        "request": request,
        "student_id": student_id,
        "error": None
    })

@app.post("/ads/create", response_class=HTMLResponse)
async def create_ad_post(
    request: Request,
    apartment: int = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    student_id: str = Form(...)
):
    data = {
        "apartment": apartment,
        "title": title,
        "content": content,
        "student_id": student_id
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{ADS_URL}/ads/create", data=data)
            if response.status_code == 200:
                return RedirectResponse(url=f"/ads?student_id={student_id}", status_code=302)
    except Exception:
        pass

    return templates.TemplateResponse("create_ad.html", {
        "request": request,
        "student_id": student_id,
        "error": "Ошибка при создании объявления"
    })

@app.get("/ads/mine", response_class=HTMLResponse)
async def show_my_ads(request: Request, student_id: str):
    async with httpx.AsyncClient() as client:
        ads_response = await client.get(f"{ADS_URL}/ads")
    ads = [ad for ad in ads_response.json() if ad.get("student_id") == 
student_id]
    return templates.TemplateResponse("my_ads.html", {
        "request": request,
        "ads": ads,
        "student_id": student_id
    })

@app.post("/ads/{ad_id}/delete")
async def delete_ad(ad_id: str, student_id: str = Form(...)):
    async with httpx.AsyncClient() as client:
        await client.post(f"{ADS_URL}/ads/{ad_id}/delete", 
data={"student_id": student_id})
    return RedirectResponse(url=f"/ads/mine?student_id={student_id}", 
status_code=302)

@app.post("/ads/{ad_id}/toggle_hide")
async def toggle_hide_ad(ad_id: str, student_id: str = Form(...)):
    async with httpx.AsyncClient() as client:
        await client.post(f"{ADS_URL}/ads/{ad_id}/toggle_hide", 
data={"student_id": student_id})
    return RedirectResponse(url=f"/ads/mine?student_id={student_id}", 
status_code=302)

