import os
import asyncio
from pyrogram import Client, filters
from fastapi import FastAPI
import uvicorn
from threading import Thread

# 1. FastAPI Setup (Render isey turant detect kar lega)
app_web = FastAPI()

@app_web.get("/")
def read_root():
    return {"status": "Bot is Running", "owner": "6593129349"}

# 2. Bot Credentials
API_ID = 38456866
API_HASH = "30a8f347f538733a1d57dae8cc458ddc"
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"

bot = Client("LyricistBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("Zinda hoon! Render ki knife ab nahi chalegi. 😎")

# 3. Running both FastAPI and Bot
async def run_bot():
    print("🚀 Starting Telegram Bot...")
    await bot.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Bot ko background thread mein chalao
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    
    # FastAPI ko main thread mein chalao (Isse Port error nahi aayega)
    port = int(os.environ.get("PORT", 8080))
    print(f"📡 Starting Web Server on port {port}")
    uvicorn.run(app_web, host="0.0.0.0", port=port)
