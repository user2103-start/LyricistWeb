import os
import sys

# Error checking for missing libraries
try:
    import asyncio
    from pyrogram import Client, filters
    from flask import Flask
    from threading import Thread
except ImportError as e:
    print(f"❌ Missing Library: {e}")
    sys.exit(1)

web = Flask(__name__)
@web.route('/')
def home(): return "Bot is Alive!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web.run(host="0.0.0.0", port=port)

# Credentials
API_ID = 38456866
API_HASH = "30a8f347f538733a1d57dae8cc458ddc"
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"

app = Client("LyricistBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def start_bot():
    Thread(target=run_web, daemon=True).start()
    await app.start()
    print("✅ BOT STARTED SUCCESSFULLY")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_bot())
    except Exception as e:
        print(f"❌ Fatal Error: {e}")
