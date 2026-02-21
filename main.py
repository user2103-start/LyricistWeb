import os
import asyncio
import threading
import requests
from flask import Flask
from pyrogram import Client, filters

# --- 🌐 WEB SERVER (RENDER HEALTH CHECK) ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "LyricistBot is Active! 🎧"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# --- 🟢 BOT CONFIG ---
API_ID = 38456866
API_HASH = "30a8f347f538733a1d57dae8cc458ddc"
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"

app = Client("LyricistBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("song"))
async def innertune_engine(client, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Gaane ka naam likho!")
    
    query = " ".join(message.command[1:])
    m = await message.reply_text("🔍 **Searching on YT Music...**")
    
    try:
        search_url = f"https://api.vyt-dlp.workers.dev/search?q={query}"
        search_res = requests.get(search_url).json()
        
        track = search_res['results'][0]
        video_id = track['id']
        title = track['title']
        
        dl_link = f"https://api.vyt-dlp.workers.dev/download?id={video_id}"
        file_path = f"{title}.mp3".replace("/", "") # File name safety

        await m.edit(f"📥 **Downloading:** {title}")
        
        r = requests.get(dl_link)
        with open(file_path, 'wb') as f:
            f.write(r.content)

        await message.reply_audio(audio=open(file_path, 'rb'), title=title)
        os.remove(file_path)
        await m.delete()

    except Exception as e:
        await m.edit(f"❌ Error: {str(e)[:50]}")

# --- 🛠️ THE ACTUAL FIX FOR RENDER ---
async def main():
    # Flask ko alag thread mein chalao
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Bot ko start karo aur idle rakho
    await app.start()
    print("✅ Bot is Live and Engine is Ready!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Naya event loop create karke use set karna
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
