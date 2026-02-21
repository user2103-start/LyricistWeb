import telebot
import requests
import sqlite3
import os
import time
import threading
from urllib.parse import quote
from flask import Flask

# --- 🌐 WEB SERVER FOR RENDER (Health Check) ---
server = Flask('')
@server.route('/')
def home(): return "LyricistsBot is Live! 🚀"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    server.run(host='0.0.0.0', port=port)

# --- 🟢 CONFIG ---
BOT_TOKEN = '8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg'
ADMIN_IDS = [6593129349] # Tera Saved ID
GENIUS_TOKEN = 'w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww'
API_BASE = "https://api.vyt-dlp.workers.dev" # Stable InnerTune Bridge

bot = telebot.TeleBot(BOT_TOKEN)

# SQLite setup
conn = sqlite3.connect('bot.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS stats (user_id INT, query TEXT, timestamp TEXT)')
conn.commit()

def genius_lyrics(query):
    url = f"https://api.genius.com/search?q={quote(query)}"
    headers = {'Authorization': f'Bearer {GENIUS_TOKEN}'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        if data['response']['hits']:
            lyrics_path = data['response']['hits'][0]['result']['url']
            return f"Check full lyrics here: {lyrics_path}"
    except: pass
    return "Lyrics temporarily unavailable 😅"

def safe_download(url, filename):
    try:
        resp = requests.get(url, stream=True, timeout=20)
        with open(filename, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return filename
    except: return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎵 *LyricistsBot* Active!\n\nGaane ka naam bhejo bhai! 🚀", parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_song(message):
    query = message.text.strip()
    user_id = message.from_user.id
    cursor.execute("INSERT INTO stats VALUES (?, ?, ?)", (user_id, query, time.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    status_msg = bot.reply_to(message, "🔍 Searching high quality audio...")
    
    try:
        # Using the stable InnerTune logic
        search_res = requests.get(f"{API_BASE}/search?q={query}").json()
        if not search_res.get('results'):
            return bot.edit_message_text("❌ Nahi mila bhai!", message.chat.id, status_msg.id)
        
        track = search_res['results'][0]
        bot.edit_message_text(f"⬇️ Downloading: {track['title']}", message.chat.id, status_msg.id)
        
        filename = f"temp_{int(time.time())}.mp3"
        dl_url = f"{API_BASE}/download?id={track['id']}"
        audio_file = safe_download(dl_url, filename)
        
        lyrics = genius_lyrics(f"{track['title']}")
        
        with open(audio_file, 'rb') as f:
            bot.send_audio(message.chat.id, f, caption=f"🎵 {track['title']}\n\n📝 {lyrics}")
        
        os.remove(audio_file)
        bot.delete_message(message.chat.id, status_msg.id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)[:50]}", message.chat.id, status_msg.id)

# --- 🚀 RUNNER ---
if __name__ == "__main__":
    # Start Flask in background
    threading.Thread(target=run_web, daemon=True).start()
    print("🚀 Bot started - Pure Sync Mode!")
    bot.infinity_polling()
