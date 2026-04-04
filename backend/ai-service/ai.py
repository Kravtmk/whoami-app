import os, requests
from groq import Groq
from fastapi import FastAPI
from pydantic import BaseModel

API = os.getenv("API_BASE_URL", "http://api:8000").rstrip("/")
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)


app = FastAPI()


class Msg(BaseModel):
    user_id: str
    text: str
    display_name: str | None = None


@app.post("/chat")
async def chat(msg: Msg):
    data = {}

    # 1) пробуем подтянуть данные с API (не обязательно, если упало — живём дальше)
    try:
        data = api_today(int(msg.user_id), msg.display_name)
    except Exception as e:
        print(f"api_today error: {e}")
        data = {}

    # 2) имя пользователя (берём из API, иначе из msg, иначе user_id)
    user = data.get("user", {}) if isinstance(data, dict) else {}
    name = user.get("displayName") or msg.display_name or str(msg.user_id)

    fact = f"Today data for user {name} ({msg.user_id}): {data}"

    # 3) ответ LLM
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "..."},
                {"role": "system", "content": fact},
                {"role": "user", "content": msg.text},
            ],
            temperature=0.7,
            max_tokens=350,
        )
        reply = completion.choices[0].message.content
        return {"reply": reply}

    except Exception as e:
        print(f"Ошибка Groq: {e}")
        return {"reply": "Енотик съел слишком много пасты и уснул... Попробуй ещё раз 😴"}

def api_today(telegram_id: int, display_name: str | None = None):
    params = {"userId": telegram_id}
    if display_name:
        params["displayName"] = display_name
    r = requests.get(f"{API}/today", params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def api_add_segment(user_id: str, role_id: int, minutes: int, note: str | None = None):
    payload = {"roleId": role_id, "minutes": minutes}
    if note:
        payload["note"] = note
    r = requests.post(f"{API}/today/segment", params={"userId": user_id}, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()
