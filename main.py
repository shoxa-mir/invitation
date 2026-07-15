import json
import os
import time
import urllib.request

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI()

# The site on GitHub Pages posts RSVPs here from a different origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://shoxa-mir.github.io"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


class Rsvp(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    attending: bool
    guests: int = Field(ge=0, le=10)
    lang: str = Field(default="uz", max_length=5)


@app.post("/rsvp")
def receive_rsvp(rsvp: Rsvp):
    # Local backup first: the response survives even if Telegram is down.
    record = {
        "name": rsvp.name,
        "attending": rsvp.attending,
        "guests": rsvp.guests,
        "lang": rsvp.lang,
        "at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open("rsvps.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        status = (
            f"✅ Keladi — {rsvp.guests} kishi" if rsvp.attending else "❌ Kela olmaydi"
        )
        text = f"💌 Yangi javob ({rsvp.lang})\n👤 {rsvp.name}\n{status}"
        data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": text}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(req, timeout=10)
        except OSError:
            pass  # already saved to rsvps.jsonl above

    return {"ok": True}


# Serve index.html at "/" and every other file (support.js, image-slot.js,
# assets/, .image-slots.state.json) as static content. Mounted last so the
# /rsvp route above matches first.
app.mount("/", StaticFiles(directory=".", html=True), name="site")
