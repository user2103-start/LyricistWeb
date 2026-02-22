import telebot
import requests
import os
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import lyricsgenius
from urllib.parse import quote

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

MUSIC_API = "https://free-music-api2.vercel.app"

# Anti-409 Protection
print("🔄 **Starting bot with 409 protection...**")
time.sleep(5)  # Wait for old instance to die

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

# Genius
genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False)

print("✅ **Bot initialized!**")

# ==================== STRICT FORCE SUBSCRIBE ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# Song + Lyrics functions (same as before)
def get_exact_song(query):
    try:
        search_url = f"{MUSIC_API}/getSongs?q={quote(query)}"
        resp = requests.get(search_url, timeout=10).json()
        
        if isinstance(resp, list) and len(resp) > 0:
            for song in resp:
                title = (song.get('title') or '').lower()
                if query.lower() in title:
                    return {
                        'url': song.get('download_url') or song.get('url'),
                        'title': song.get('title', query),
                        'artist': song.get('artist', 'Artist'),
                        'success': True
                    }
            song = resp[0]
            return {
                'url': song.get('download_url') or song.get('url'),
                'title': song.get('title', query),
                'artist': song.get('artist', 'Artist'),
                'success': True
            }
    except:
        pass
    return {'success': False}

def get_exact_lyrics(query):
    try:
        songs = genius.search(query)
        if songs:
            for song in songs:
                title = song.title.lower()
                if query.lower() in title:
                    lyrics = genius.lyrics(song.id)
                    return format_lyrics(song.title, song.artist, lyrics)
    except:
        pass
    return None

def format_lyrics(title, artist, lyrics):
    lines = [line.strip() for line in lyrics.split('\n') if line.strip()][:15]
    formatted = f"🎤 **{title}**\n👤 **{artist}**\n\n"
    for line in lines:
        formatted += f"**`{line}`**\n"
    return formatted

# ==================== COMMANDS ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    is_admin = user_id == ADMIN_ID
    
    if is_admin:
        bot.send_message(message.chat.id, 
            "🔥 **ADMIN ONLINE!** 🔥\n\n"
            "**Commands:**\n`/song gehra hua`\n`/songLY gehra hua`\n`/admin`", 
            parse_mode='Markdown')
    else:
        if not is_subscribed(user_id):
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("📢 JOIN NOW", url="https://t.me/+JPgViOHx7bdlMDZl")
            )
            bot.send_message(message.chat.id, 
                "🚫 **BOT LOCKED!**\n\n📢 **Channel join karo pehle!**\n"
                "**Then:** `/song songname`", 
                reply_markup=markup, parse_mode='Markdown')
            return
        
        bot.send_message(message.chat.id, 
            "🎤 **READY!** 🎵\n\n"
            "**Use:**\n`/song gehra hua`\n`/songLY gehra hua`", 
            parse_mode='Markdown')

@bot.message_handler(commands=['song'])
def song_only(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Channel join first!**")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ **/song SONGNAME**")
        return
    
    music = get_exact_song(query)
    if music['success']:
        try:
            bot.send_audio(message.chat.id, music['url'], 
                          caption=f"🎵 **{music['title']}** | 320kbps 🎵",
                          parse_mode='Markdown')
            bot.reply_to(message, "✅ **Song delivered!** 🎵")
        except Exception as e:
            bot.reply_to(message, f"❌ **Download error:** {str(e)[:50]}")
    else:
        bot.reply_to(message, f"❌ **{query}** not found!")

@bot.message_handler(commands=['songLY'])
def song_lyrics(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Channel join first!**")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ **/songLY SONGNAME**")
        return
    
    # Song
    music = get_exact_song(query)
    if music['success']:
        try:
            bot.send_audio(message.chat.id, music['url'], 
                          caption=f"🎵 **{music['title']}** | 320kbps 🎵",
                          parse_mode='Markdown')
        except:
            pass
    
    # Lyrics
    lyrics = get_exact_lyrics(query)
    if lyrics:
        bot.send_message(message.chat.id, lyrics, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, f"❌ **{query}** lyrics not found!")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"))
    markup.row(InlineKeyboardButton("📊 Stats", callback_data="stats"))
    
    bot.send_message(message.chat.id, "🔥 **ADMIN PANEL** 🔥", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def admin_cb(call):
    if call.from_user.id != ADMIN_ID: return
    
    if call.data == "broadcast":
        bot.send_message(call.message.chat.id, "📢 Send broadcast:")
        bot.register_next_step_handler(bot.send_message(call.message.chat.id, "📢 Message:"), lambda m: admin_broadcast(m, call.message.chat.id))
    elif call.data == "stats":
        bot.edit_message_text("📊 **Bot Live & Healthy!** ✅", call.message.chat.id, call.message.id)

def admin_broadcast(message, chat_id):
    try:
        bot.send_message(CHANNEL_ID, message.text)
        bot.send_message(chat_id, "✅ **Broadcast sent!**")
    except:
        bot.send_message(chat_id, "❌ **Broadcast failed!**")

# ==================== ANTI-CRASH POLLING ====================
print("🚀 **Starting polling...**")
while True:
    try:
        bot.infinity_polling(none_stop=True, interval=1, timeout=20)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔄 Restarting in 10s...")
        time.sleep(10)
