import os
from groq import Groq
from fastapi import FastAPI
from pydantic import BaseModel

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

app = FastAPI()

class Msg(BaseModel):
    user_id: str 
    text: str 

@app.post("/chat")
async def chat(msg: Msg):
    try:        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": "Ты — Енотик Рикки из Палермо. Ты добрый, веселый, любишь Python и сицилийские аранчини. Отвечай детям кратко, с эмодзи. 🦝🍋"
                },
                {
                    "role": "user", 
                    "content": msg.text
                }
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        reply = completion.choices[0].message.content
        return {"reply": reply}
        
    except Exception as e:
        print(f"Ошибка Groq: {e}")
        return {"reply": "Енотик съел слишком много пасты и уснул... Попробуй еще раз! 🍝💤"}
