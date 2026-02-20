import os
import asyncio
import requests
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# --- Flask for Cron-job ---
web = Flask(__name__)
@web.route('/')
def home(): return "Music Bot is Active! 🎸"

def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- Credentials ---
API_ID = 38456866
API_HASH = "30a8f347f538733a1d57dae8cc458ddc"
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"
YT_API_KEY = "AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX3" # Tera extracted key

app = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Search Function (Using OuterTune Logic) ---
def yt_search(query):
    url = f"https://music.youtube.com/youtubei/v1/search?key={YT_API_KEY}"
    headers = {
        "User-Agent": "com.google.android.apps.youtube.music/6.41.51 (Linux; U; Android 12)",
        "X-YouTube-Client-Name": "67",
        "X-YouTube-Client-Version": "6.41.51"
    }
    payload = {
        "context": {"client": {"clientName": "ANDROID_MUSIC", "clientVersion": "6.41.51"}},
        "query": query
    }
    r = requests.post(url, headers=headers, json=payload)
    # Yahan se results filter hote hain...
    return r.json()

@app.on_message(filters.command("play"))
async def play(client, message):
    query = message.text.split(None, 1)[1]
    await message.reply_text(f"🔍 Searching for **{query}** using extracted API...")
    # Search logic and playback here...

# --- The Main Entry Point (Solves Screenshot Errors) ---
async def start_bot():
    # 1. Start Flask in a background thread
    Thread(target=run_web, daemon=True).start()
    
    # 2. Start Pyrogram Client
    print("🚀 Bot starting...")
    await app.start()
    print("✅ Bot is online on Render!")
    
    # 3. Keep the loop alive
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Ye part tere loop error ko fix karega
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
