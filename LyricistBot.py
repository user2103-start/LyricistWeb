import os
import asyncio
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# --- Flask Server ---
web = Flask(__name__)

@web.route('/')
def home():
    return "Bot is Alive! 🚀"

def run_web():
    # Render default port 8080 use karta hai
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- Bot Config ---
API_ID = 38456866
API_HASH = "30a8f347f538733a1d57dae8cc458ddc"
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"

app = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def main():
    # Flask ko background mein start karo
    Thread(target=run_web, daemon=True).start()
    
    # Bot ko start karo
    print("Starting Bot...")
    await app.start()
    print("Bot is Online!")
    
    # Bot ko idle rakho taaki chalta rahe
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        # Loop handle karne ka naya tareeka
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
