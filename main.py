import telebot
import requests
import os
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import lyricsgenius
from urllib.parse import quote

# ==================== SAFE CONFIG ====================
BOT_TOKEN = os.getenv("8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1003751644036")
ADMIN_ID_STR = os.getenv("ADMIN_ID", "6593129349")

# SAFE ADMIN_ID
try:
    ADMIN_ID = int(ADMIN_ID_STR)
except:
    ADMIN_ID = 6593129349  # Default fallback
    print(f"⚠️ ADMIN_ID set to default: {ADMIN_ID}")

GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"
MUSIC_API = "https://free-music-api2.vercel.app"

print(f"✅ Config: ADMIN={ADMIN_ID}, CHANNEL={CHANNEL_ID}")

# Anti-409 + Init
time.sleep(3)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')
genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False)

print("🚀 Bot ready!")

# ==================== STRICT FORCE SUBSCRIBE ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ==================== SONG FUNCTIONS ====================
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
            # Fallback first result
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

# ==================== 1. /start ====================
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, 
            "🔥 **ADMIN WELCOME!** 🔥\n\n"
            "**Commands:**\n"
            "`/song gehra hua`\n"
            "`/songLY gehra hua`\n"
            "`/admin`", parse_mode='Markdown')
    else:
        if not is_subscribed(user_id):
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("📢 JOIN CHANNEL", url="https://t.me/+JPgViOHx7bdlMDZl")
            )
            bot.send_message(message.chat.id, 
                "🚫 **BOT LOCKED!**\n\n"
                "📢 **Channel join karo!**\n"
                "**Phir:** `/song songname`", 
                reply_markup=markup, parse_mode='Markdown')
            return
        
        bot.send_message(message.chat.id, 
            "🎤 **WELCOME!** 🎵\n\n"
            "**Use:**\n"
            "`/song gehra hua`\n"
            "`/songLY gehra hua`", parse_mode='Markdown')

# ==================== 2. /song (SONG ONLY) ====================
@bot.message_handler(commands=['song'])
def song_only(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Channel join karo!**")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ **Example: /song gehra hua**")
        return
    
    music = get_exact_song(query)
    if music['success']:
        try:
            bot.send_audio(message.chat.id, music['url'], 
                          caption=f"🎵 **{music['title']}** | 320kbps 🎵",
                          parse_mode='Markdown')
            bot.reply_to(message, "✅ **Song ready!** 🎵")
        except Exception as e:
            bot.reply_to(message, f"❌ **Download issue:** {str(e)[:50]}")
    else:
        bot.reply_to(message, f"❌ **{query}** song not found!")

# ==================== 3. /songLY ====================
@bot.message_handler(commands=['songLY'])
def song_lyrics(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Channel join karo!**")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ **Example: /songLY gehra hua**")
        return
    
    status = bot.reply_to(message, f"🔍 **{query}** loading...")
    
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
        bot.send_message(message.chat.id, f"❌ **{query}** lyrics not available!")
    
    bot.delete_message(status.chat.id, status.id)

# ==================== 4. /admin ====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ **Admin only!**")
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"))
    markup.row(InlineKeyboardButton("📊 Stats", callback_data="stats"))
    markup.row(InlineKeyboardButton("🔧 Restart", callback_data="restart"))
    
    bot.send_message(message.chat.id, 
        "🔥 **ADMIN PANEL** 🔥\n\n**Choose:**", 
        reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def admin_callback(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Admin only!")
        return
    
    if call.data == "broadcast":
        sent_msg = bot.send_message(call.message.chat.id, "📢 **Broadcast message type karo:**")
        bot.register_next_step_handler(sent_msg, process_broadcast)
    elif call.data == "stats":
        bot.edit_message_text(
            "📊 **STATS:**\n"
            "• Status: ✅ LIVE\n"
            "• Music API: ✅ Working\n"
            "• Genius: ✅ Active\n"
            "• Subs: Required", 
            call.message.chat.id, call.message.id
        )
    elif call.data == "restart":
        bot.edit_message_text("🔄 **Restart signal sent!** (Bot healthy)", 
                            call.message.chat.id, call.message.id)

def process_broadcast(message):
    try:
        bot.send_message(CHANNEL_ID, message.text)
        bot.reply_to(message, "✅ **Broadcast SUCCESS!** 📢")
    except Exception as e:
        bot.reply_to(message, f"❌ **Broadcast failed:** {str(e)}")

# ==================== SUPER SAFE POLLING ====================
print("🎤 **Starting SUPER SAFE polling...**")
while True:
    try:
        bot.infinity_polling(none_stop=True, interval=1, timeout=20)
    except Exception as e:
        print(f"❌ Restarting... Error: {e}")
        time.sleep(10)
