import os
import asyncio
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# 1. Flask Server setup
web = Flask(__name__)

@web.route('/')
def home():
    return "Bot is Alive! 🚀"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host="0.0.0.0", port=port)

# 2. Bot Credentials
API_ID = 38456866
API_HASH = "30a8f347f538733a1d57dae8cc458ddc"
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"

app = Client("LyricistBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Zinda hoon bhai! Render ki knife se bach nikla. 😎")

# 3. Tank-Proof Runner Logic
async def main():
    # Flask ko background thread mein start karo
    Thread(target=run_web, daemon=True).start()
    
    print("Bot starting...")
    async with app:
        print("✅ BOT IS LIVE!")
        # Isse bot chalta rahega bina loop crash kiye
        await asyncio.Event().wait()

if __name__ == "__main__":
    # Naye Python versions ke liye sabse safe tareeka
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    except RuntimeError:
        # Agar loop pehle se chal raha ho (rare case on Render)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
