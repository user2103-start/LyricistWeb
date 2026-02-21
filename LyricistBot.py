import os
import asyncio
import threading
import requests
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- 🌐 WEB SERVER ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "InnerTune Engine is Live! 🎧"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- 🟢 CONFIG ---
API_ID = 38456866
API_HASH = "30a8f347f538733a1d57dae8cc458ddc"
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"
SUDO_USER = 6593129349

app = Client("LyricistBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- 🎵 INNER-TUNE DOWNLOADER (BY-PASSING BLOCK) ---
# Hum ek public YT-Music API bridge use karenge jo InnerTune ke logic par chalta hai
BRIDGE_API = "https://yt-music-api-nine.vercel.app/download?id="

@app.on_message(filters.command("song"))
async def innertune_engine(client, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Gaane ka naam batao bhai!")
    
    query = " ".join(message.command[1:])
    m = await message.reply_text("🔍 **InnerTune Engine dhoond raha hai...**")
    
    try:
        # Step 1: Search (Hum YT search use karenge id nikaalne ke liye)
        search_url = f"https://api.vyt-dlp.workers.dev/search?q={query}"
        search_res = requests.get(search_url).json()
        
        if not search_res or 'results' not in search_res:
            return await m.edit("❌ YT Music par gaana nahi mila.")

        video_id = search_res['results'][0]['id']
        title = search_res['results'][0]['title']
        thumb = search_res['results'][0]['thumbnail']
        duration = search_res['results'][0]['duration']

        await m.edit(f"📥 **Downloading High Quality Audio...**\n🎵 {title}")

        # Step 2: Download using InnerTune's stable logic
        dl_link = f"https://api.vyt-dlp.workers.dev/download?id={video_id}"
        file_path = f"{title}.mp3"
        
        r = requests.get(dl_link)
        with open(file_path, 'wb') as f:
            f.write(r.content)

        # Step 3: Send with Metadata
        await message.reply_audio(
            audio=open(file_path, 'rb'),
            title=title,
            duration=int(duration) if duration else 0,
            caption=f"✅ **Downloaded via InnerTune Engine**\n\n🎵 **Title:** {title}\n🆔 **ID:** `{video_id}`",
            thumb=requests.get(thumb, stream=True).raw if thumb else None
        )
        
        os.remove(file_path)
        await m.delete()

    except Exception as e:
        await m.edit(f"❌ InnerTune Error: {str(e)[:50]}")

# --- 🚀 RUNNER ---
async def start_bot():
    threading.Thread(target=run_web, daemon=True).start()
    await app.start()
    print("✅ LyricistBot (InnerTune Edition) is Live!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())
