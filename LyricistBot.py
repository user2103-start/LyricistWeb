import os
import asyncio
from pyrogram import Client, filters
from flask import Flask
from threading import Thread

# 1. Flask Setup (Isi se Render ko 'Zinda' hone ka signal milega)
web = Flask(__name__)

@web.route('/')
def home():
    return "Bot is Live! 🚀"

def run_web():
    # Render hamesha PORT environment variable bhejta hai
    # Isko milte hi Render ka 'No open ports' error gayab ho jayega
    port = int(os.environ.get("PORT", 8080))
    web.run(host="0.0.0.0", port=port)

# 2. Bot Credentials
API_ID = 38456866
API_HASH = "30a8f347f538733a1d57dae8cc458ddc"
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"

app = Client("LyricistBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Zinda hoon! Render ne port dhoond liya. 😎")

# 3. Ultimate Runner
async def main():
    # Flask ko pehle start karo taaki Render ko port mil jaye
    server_thread = Thread(target=run_web)
    server_thread.daemon = True
    server_thread.start()
    
    print("🚀 Starting Bot...")
    async with app:
        print("✅ BOT IS LIVE ON TELEGRAM!")
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
