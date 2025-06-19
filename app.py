
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import openai
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    text: str

site_info = {
    "site_name": "Chabad House Palm Beach",
    "location": "Palm Beach, FL",
    "address": "361 South County Road Suite #D, Palm Beach, FL 33480",
    "phone": "561-659-3884",
    "email": "office@palmbeachjewish.com",
    "rabbi": "Rabbi Zalman Levitin",
    "geo": {"lat": 26.7056, "lon": -80.0364},
    "weekly_schedule": {
        "fri": "6pm winter / 7pm summer services",
        "sat": ["9:00 AM Kabbalah Café", "9:30 AM Services + Kiddush"],
        "sun": ["8:30 AM Minyan & Breakfast", "Sunday Tefillin Club"],
        "mon": ["8AM Tefillin Club + class", "10:15 AM Women's 'Caffeine for the Soul'", "8pm Pure Chassidus"],
        "tue": ["7:30 PM Torah Studies"]
    }
}

def get_candle_lighting(lat, lon):
    url = f"https://www.hebcal.com/shabbat/?cfg=json&geonameid=4167499&m=50"
    response = requests.get(url)
    data = response.json()
    candle = havdalah = None
    for item in data.get("items", []):
        if item["category"] == "candles" and not candle:
            candle = f"{item['title']} on {item['date']}"
        elif item["category"] == "havdalah" and not havdalah:
            havdalah = f"{item['title']} on {item['date']}"
        if candle and havdalah:
            break
    return f"Candle lighting: {candle}\nHavdalah: {havdalah}" if candle and havdalah else "Sorry, I couldn't fetch candle lighting times."

@app.post("/chat")
async def chat(message: Message):
    msg = message.text.lower()

    if "candle lighting" in msg or "shabbat time" in msg or "havdalah" in msg:
        return {"reply": get_candle_lighting(site_info["geo"]["lat"], site_info["geo"]["lon"])}

    prompt = f"You are a helpful assistant for {site_info['site_name']} located in {site_info['location']}. The rabbi is {site_info['rabbi']}. Address: {site_info['address']}. Phone: {site_info['phone']}. Email: {site_info['email']}. Weekly schedule includes: {site_info['weekly_schedule']}."

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message.text}
            ]
        )
        return {"reply": response.choices[0].message["content"]}
    except Exception as e:
        return {"reply": f"Sorry, something went wrong: {str(e)}"}
