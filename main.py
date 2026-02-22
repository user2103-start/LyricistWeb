import telebot
import requests
import time
import asyncio
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import lyricsgenius
from urllib.parse import quote

# ==================== CONFIG ====================
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"
CHANNEL_ID = "-1003751644036"
CHANNEL_LINK = "https://t.me/+JPgViOHx7bdlMDZl"  # ✅ YE ADD!
ADMIN_ID = 6593129349
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

MUSIC_API = "https://free-music-api2.vercel.app"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

# Genius setup
genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False)

# Anti-409 protection
time.sleep(5)

print("🎨 VISUAL LYRICS BOT STARTING...")

# ==================== FORCE SUBSCRIBE ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ==================== MUSIC ENGINE ====================
def get_song(query):
    try:
        search_url = f"{MUSIC_API}/getSongs?q={quote(query)}"
        resp = requests.get(search_url, timeout=10).json()
        if isinstance(resp, list) and len(resp) > 0:
            song = resp[0]  # Best match
            return {
                'url': song.get('download_url') or song.get('url'),
                'title': song.get('title', query),
                'success': True
            }
    except:
        pass
    return {'success': False}

# ==================== VISUAL LYRICS 🎨 ====================
def get_visual_lyrics(query):
    try:
        songs = genius.search(query)
        if songs and len(songs) > 0:
            song = songs[0]
            lyrics = genius.lyrics(song.id)
            
            # Visual formatting - LINE BY LINE with emojis!
            lines = [line.strip() for line in lyrics.split('\n') if line.strip()][:20]
            visual_lyrics = "🎤 **VISUAL LYRICS** 🎵\n\n"
            
            for i, line in enumerate(lines, 1):
                if i % 2 == 0:
                    visual_lyrics += f"**`{line}`** 🎶\n"
                else:
                    visual_lyrics += f"`{line}` ✨\n"
            
            visual_lyrics += f"\n👤 **{song.artist}**\n🎵 **{song.title}**"
            return visual_lyrics
    except:
        pass
    return None

# ==================== COMMANDS ====================

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    
    # Welcome message - NO copyright stuff!
    welcome = (
        "🎨 **Welcome to VISUAL LYRICS!** 🚀\n\n"
        "🌟 **Most Advanced Music Bot on Telegram!**\n\n"
        "**Commands:**\n"
        "🎵 `/song songname` → Premium Audio\n"
        "🎤 `/songLY songname` → **VISUAL LYRICS**\n"
        "🔥 `/admin` → Admin Panel"
    )
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, welcome + "\n\n👑 **ADMIN MODE ACTIVE**")
    else:
        if not is_subscribed(user_id):
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK)  # ✅ YE LINK!
            )
            bot.send_message(message.chat.id, 
                "🚫 **VISUAL LYRICS LOCKED!**\n\n"
                "📢 **Join channel first:**\n"
                f"[Click here]({CHANNEL_LINK})\n\n"
                "✅ Join → `/start` again!", 
                reply_markup=markup, disable_web_page_preview=True)
            return
        
        bot.send_message(message.chat.id, welcome)

@bot.message_handler(commands=['song'])
def song_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Join channel first!**")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/song tum hi ho`")
        return
    
    bot.reply_to(message, f"🎵 **{query}** loading...")
    
    music = get_song(query)
    if music['success']:
        try:
            bot.send_audio(message.chat.id, music['url'], 
                          caption=f"🎵 **{music['title']}** | Premium Quality 🎵",
                          title=music['title'])
            bot.reply_to(message, "✅ **Song delivered!** 🎶")
        except:
            bot.reply_to(message, "❌ **Download failed! Try again.**")
    else:
        bot.reply_to(message, f"❌ **`{query}`** not found!")

@bot.message_handler(commands=['songLY'])
def songlyrics_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Join channel first!**")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/songLY kal ho naa ho`")
        return
    
    bot.reply_to(message, f"🎨 **VISUAL LYRICS** for `{query}` loading...")
    
    # Song first
    music = get_song(query)
    if music['success']:
        try:
            bot.send_audio(message.chat.id, music['url'], 
                          caption=f"🎵 **{music['title']}** 🎤 Visual Lyrics coming!",
                          title=music['title'])
        except:
            pass
    
    # Visual Lyrics
    lyrics = get_visual_lyrics(query)
    if lyrics:
        bot.send_message(message.chat.id, lyrics)
    else:
        bot.send_message(message.chat.id, f"❌ **Visual lyrics** for `{query}` not available!")

@bot.message_handler(commands=['admin'])
def admin_handler(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Broadcast", callback_data="bc"))
    markup.row(InlineKeyboardButton("📊 Stats", callback_data="stats"))
    
    bot.send_message(message.chat.id, 
        "🔥 **VISUAL LYRICS ADMIN** 🔥\n\n📊 Users: LIVE\n🎵 Songs: 1000+\n🎤 Lyrics: Genius API",
        reply_markup=markup)

# Admin callbacks (same as before)
@bot.callback_query_handler(func=lambda call: True)
def admin_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    if call.data == "bc":
        bot.send_message(call.message.chat.id, "📢 **Broadcast message:**")
        bot.register_next_step_handler(call.message, lambda m: broadcast(m, call.message.chat.id))
    elif call.data == "stats":
        bot.edit_message_text("✅ **ALL SYSTEMS GREEN!** 🚀", call.message.chat.id, call.message.id)

def broadcast(message, chat_id):
    try:
        bot.send_message(CHANNEL_ID, message.text)
        bot.send_message(chat_id, "✅ **Broadcast sent!** 📢")
    except Exception as e:
        bot.send_message(chat_id, f"❌ **Error:** {str(e)}")

# ==================== FAIL-SAFE START ====================
if __name__ == "__main__":
    print("🎨 VISUAL LYRICS BOT LIVE!")
    try:
        bot.infinity_polling(none_stop=True, interval=2, timeout=30)
    except Exception as e:
        print(f"❌ Restarting... {e}")
        time.sleep(10)
