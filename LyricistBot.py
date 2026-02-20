import os
import asyncio
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# --- 1. Flask Server (Cron-job ke liye) ---
web = Flask(__name__)

@web.route('/')
def home():
    return "Bot is Alive! 🎸"

def run_web():
    # Render automatically PORT environment variable deta hai
    port = int(os.environ.get("PORT", 8080))
    web.run(host="0.0.0.0", port=port)

# --- 2. Bot Configuration ---
# Tune jo data diya tha wahi use kar raha hoon
API_ID = 38456866
API_HASH = "30a8f347f538733a1d57dae8cc458ddc"
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"
OWNER_ID = 6593129349

app = Client(
    "LyricistBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- 3. Simple Command ---
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(f"Oye {message.from_user.first_name}! Bot setup done hai. 🚀")

# --- 4. Main Runner (The Waiter Logic Fixed) ---
async def start_everything():
    # Flask ko background mein chalao
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
    
    print("Starting Bot...")
    await app.start()
    print("✅ Bot is Online on Render!")
    
    # Ye line bot ko band hone se rokegi
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Render ke loop error ka permanent solution
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_everything())
    except RuntimeError:
        # Agar loop nahi milta toh naya banao
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(start_everything())
