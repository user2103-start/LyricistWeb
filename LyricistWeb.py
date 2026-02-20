import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- Flask Server for Cron-job.org ---
web = Flask(__name__)

@web.route('/')
def home():
    return "Bot is Running!"

def run_web():
    web.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- Bot Configuration ---
API_ID = 38456866
API_HASH = "30a8f347f538733a1d57dae8cc458ddc"
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"
OWNER_ID = 6593129349
FSUB_CHANNEL = -1003751644036

app = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Auto Delete Function ---
async def auto_delete(message, delay):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

@app.on_message(filters.command("play"))
async def play_song(client, message):
    # (Teri search aur stream logic yahan aayegi)
    m = await message.reply_text("🎶 Playing: Song Name...\n\n_This file will auto-delete in 10 minutes to avoid copyright._")
    
    # Maan lo humne audio bhej di
    # audio_msg = await message.reply_audio(...)
    
    # 600 seconds = 10 minutes baad delete
    asyncio.create_task(auto_delete(m, 600))
    # asyncio.create_task(auto_delete(audio_msg, 600))

if __name__ == "__main__":
    # Web server ko alag thread mein chalana zaroori hai
    Thread(target=run_web).start()
    print("Web server and Bot starting...")
    app.run()
