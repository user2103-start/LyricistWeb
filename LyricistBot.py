import os
import asyncio
from pyrogram import Client, filters
from fastapi import FastAPI
import uvicorn

# 1. FastAPI Setup (Render ki Web Service ke liye compulsory hai)
app_web = FastAPI()

@app_web.get("/")
def home():
    return {"status": "Bot is Running", "devil_killed": True}

# 2. Bot Credentials
API_ID = 38456866
API_HASH = "30a8f347f538733a1d57dae8cc458ddc"
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"

bot = Client("LyricistBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("Zinda hoon! Web Service pe kabza kar liya hai. 😎")

# 3. Main Logic: FastAPI ke saath Bot ko start karna
@app_web.on_event("startup")
async def start_bot():
    # Ye line bot ko background mein bina loop error ke start karegi
    asyncio.create_task(bot.start())
    print("✅ Telegram Bot Started in Background")

@app_web.on_event("shutdown")
async def stop_bot():
    await bot.stop()

if __name__ == "__main__":
    # Render hamesha PORT environment variable bhejta hai
    port = int(os.environ.get("PORT", 8080))
    # Uvicorn hi main loop handle karega, isliye 'no current event loop' nahi aayega
    uvicorn.run(app_web, host="0.0.0.0", port=port)
