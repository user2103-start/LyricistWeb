import telebot
import requests
import re
import os
import time
import sqlite3
import threading
from urllib.parse import quote
from flask import Flask

# --- 🌐 WEB SERVER FOR RENDER (Health Check) ---
server = Flask('')
@server.route('/')
def home(): return "LyricistsBot (JioSaavn Engine) is Live! 🚀"

def run_web():
    # Render automatically sets the PORT variable
    port = int(os.environ.get("PORT", 10000))
    server.run(host='0.0.0.0', port=port)

# --- 🟢 CONFIG ---
BOT_TOKEN = '8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg' #
GENIUS_TOKEN = 'w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww' #
ADMIN_IDS = [6593129349] # Tera Saved ID
SAAVN_BASE = "https://saavn.me" # JioSaavn API

bot = telebot.TeleBot(BOT_TOKEN)

# --- 📁 DATABASE SETUP ---
conn = sqlite3.connect('bot.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS stats (id INTEGER PRIMARY KEY, user_id INT, query TEXT, time TEXT)')
conn.commit()

# --- 🎵 JIOSAAVN ENGINE ---
def search_saavn(query):
    url = f"{SAAVN_BASE}/search/songs?query={quote(query)}"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json().get('data', {}).get('results', [])
    except: return []

def get_lyrics(query):
    try:
        gurl = f"https://api.genius.com/search?q={quote(query)}"
        headers = {'Authorization': f'Bearer {GENIUS_TOKEN}'}
        resp = requests.get(gurl, headers=headers, timeout=8)
        hits = resp.json()['response']['hits']
        if hits:
            return f"Lyrics available at: {hits[0]['result']['url']}"
    except: pass
    return "Lyrics fetch karne ke liye gaane ka sahi naam likhein! 📝"

def download_temp(url, filename):
    try:
        resp = requests.get(url, stream=True, timeout=15)
        with open(filename, 'wb') as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return filename
    except: return None

# --- 🤖 BOT HANDLERS ---
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "🎵 *LyricistsBot (JioSaavn Edition)* Active!\n\nGaane ka naam bhejo bhai! 🚀", parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_query(message):
    query = message.text.strip()
    user_id = message.from_user.id
    cursor.execute("INSERT INTO stats (user_id, query, time) VALUES (?, ?, ?)", (user_id, query, time.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    status = bot.reply_to(message, "🔍 Searching on JioSaavn...")
    
    tracks = search_saavn(query)
    if not tracks:
        return bot.edit_message_text("❌ Song nahi mila!", status.chat.id, status.message_id)
    
    track = tracks[0]
    # JioSaavn API usually provides high-quality links in the last index of downloadUrl
    dl_url = track.get('downloadUrl', [{}])[-1].get('link') 
    
    if not dl_url:
        return bot.edit_message_text("❌ Download link blocked!", status.chat.id, status.message_id)
    
    bot.edit_message_text(f"⬇️ Downloading: {track['name']}", status.chat.id, status.message_id)
    filename = f"temp_{int(time.time())}.mp3"
    audio_file = download_temp(dl_url, filename)
    
    if not audio_file:
        return bot.edit_message_text("❌ Download failed!", status.chat.id, status.message_id)
    
    lyrics = get_lyrics(f"{track['name']} {track['artists']['primary'][0]['name']}")
    caption = f"🎵 **{track['name']}**\n👤 {track['artists']['primary'][0]['name']}\n\n{lyrics}"
    
    try:
        with open(audio_file, 'rb') as f:
            bot.send_audio(message.chat.id, f, caption=caption[:1024], parse_mode='Markdown', title=track['name'])
        os.remove(audio_file)
        bot.delete_message(status.chat.id, status.message_id)
    except Exception as e:
        bot.send_message(message.chat.id, "✅ Audio Ready! (Caption Error)")

# --- 🔧 ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id not in ADMIN_IDS:
        return bot.reply_to(message, "❌ Admin access nahi hai!")
    cursor.execute("SELECT COUNT(*) FROM stats")
    total = cursor.fetchone()[0]
    bot.reply_to(message, f"📊 Total Queries: `{total}`", parse_mode='Markdown')

# --- 🚀 RUNNER ---
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    print("🎉 Bot is Polling on JioSaavn API!")
    bot.infinity_polling(none_stop=True)
