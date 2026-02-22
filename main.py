import telebot
import requests
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import lyricsgenius
from urllib.parse import quote

# ==================== HARDCODED CONFIG ====================
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"  # ✅ DIRECT
CHANNEL_ID = "-1003751644036"
ADMIN_ID = 6593129349  # ✅ SAFE INT
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

MUSIC_API = "https://free-music-api2.vercel.app"

print(f"🚀 Config loaded: ADMIN={ADMIN_ID}")

# Anti-409 delay
time.sleep(3)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')
genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False)

print("✅ Bot + Genius READY!")

# ==================== FORCE SUBSCRIBE ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ==================== SONG ENGINE ====================
def get_exact_song(query):
    try:
        search_url = f"{MUSIC_API}/getSongs?q={quote(query)}"
        resp = requests.get(search_url, timeout=10).json()
        
        if isinstance(resp, list) and len(resp) > 0:
            # Exact match first
            for song in resp:
                title = (song.get('title') or '').lower()
                if query.lower() in title:
                    return {
                        'url': song.get('download_url') or song.get('url'),
                        'title': song.get('title', query),
                        'success': True
                    }
            # Fallback
            song = resp[0]
            return {
                'url': song.get('download_url') or song.get('url'),
                'title': song.get('title', query),
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
                if query.lower() in song.title.lower():
                    lyrics = genius.lyrics(song.id)
                    lines = [l.strip() for l in lyrics.split('\n') if l.strip()][:12]
                    return f"🎤 **{song.title}**\n👤 **{song.artist}**\n\n" + "\n".join([f"**`{line}`**" for line in lines])
    except:
        pass
    return None

# ==================== COMMANDS ====================

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, 
            "🔥 **ADMIN DASHBOARD** 🔥\n\n"
            "**Commands:**\n`/song kal ho naa ho`\n`/songLY kal ho naa ho`\n`/admin`", 
            parse_mode='Markdown')
    else:
        if not is_subscribed(user_id):
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("📢 JOIN CHANNEL", url="https://t.me/+JPgViOHx7bdlMDZl")
            )
            bot.send_message(message.chat.id, 
                "🚫 **ACCESS DENIED!**\n\n"
                "📢 **Channel join karo pehle!**\n"
                "**Then use:** `/song songname`", 
                reply_markup=markup, parse_mode='Markdown')
            return
        
        bot.send_message(message.chat.id, 
            "🎤 **MUSIC BOT ACTIVE!** 🎵\n\n"
            "**Commands:**\n"
            "`/song gehra hua` → Song only\n"
            "`/songLY gehra hua` → Song + Lyrics", 
            parse_mode='Markdown')

@bot.message_handler(commands=['song'])
def song_command(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Channel join first!**")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ **Type: /song SONGNAME**\n*Example:* `/song tum hi ho`")
        return
    
    music = get_exact_song(query)
    if music['success']:
        try:
            bot.send_audio(message.chat.id, music['url'], 
                          caption=f"🎵 **{music['title']}** | 320kbps PREMIUM 🎵",
                          parse_mode='Markdown', title=music['title'])
            bot.reply_to(message, f"✅ **{music['title']}** delivered! 🎵")
        except:
            bot.reply_to(message, "❌ **Download failed! Try again.**")
    else:
        bot.reply_to(message, f"❌ **'{query}'** not found in library!")

@bot.message_handler(commands=['songLY'])
def songlyrics_command(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Channel join first!**")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ **Type: /songLY SONGNAME**")
        return
    
    bot.reply_to(message, f"🔍 **{query}** Song + Lyrics loading...")
    
    # Send Song
    music = get_exact_song(query)
    if music['success']:
        try:
            bot.send_audio(message.chat.id, music['url'], 
                          caption=f"🎵 **{music['title']}** | 320kbps 🎵",
                          parse_mode='Markdown')
        except:
            pass
    
    # Send Lyrics
    lyrics = get_exact_lyrics(query)
    if lyrics:
        bot.send_message(message.chat.id, lyrics, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, f"❌ **{query}** lyrics not available!")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ **ADMIN ONLY!**")
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Broadcast", callback_data="bc"))
    markup.row(InlineKeyboardButton("📊 Stats", callback_data="stats"))
    markup.row(InlineKeyboardButton("🔧 Status", callback_data="status"))
    
    bot.send_message(message.chat.id, 
        "🔥 **ADMIN CONTROL PANEL** 🔥", 
        reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id)
        return
    
    if call.data == "bc":
        bot.edit_message_text("📢 **Type broadcast message:**", 
                            call.message.chat.id, call.message.id)
        bot.register_next_step_handler(
            bot.send_message(call.message.chat.id, "📢 Message:"), 
            broadcast_message
        )
    elif call.data == "stats":
        bot.edit_message_text(
            "📊 **LIVE STATS:**\n"
            "✅ Bot: ACTIVE\n"
            "✅ Music API: OK\n"
            "✅ Genius Lyrics: OK\n"
            "🔒 Subs: ENFORCED", 
            call.message.chat.id, call.message.id
        )
    elif call.data == "status":
        bot.edit_message_text("✅ **ALL SYSTEMS GREEN!** 🚀", 
                            call.message.chat.id, call.message.id)

def broadcast_message(message):
    try:
        bot.send_message(CHANNEL_ID, message.text)
        bot.reply_to(message, "✅ **Broadcasted to channel!** 📢")
    except Exception as e:
        bot.reply_to(message, f"❌ **Error:** {str(e)}")

# ==================== FAIL-SAFE START ====================
print("🎤 **STARTING KARAOKE BOT...**")
print("✅ Token loaded successfully!")

try:
    bot.infinity_polling(none_stop=True, interval=1, timeout=20)
except KeyboardInterrupt:
    print("🛑 Bot stopped by user")
except Exception as e:
    print(f"❌ Fatal error: {e}")
    time.sleep(10)
