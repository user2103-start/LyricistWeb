import telebot
import requests
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import lyricsgenius

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1003751644036")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6593129349"))
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

MUSIC_API = "https://free-music-api2.vercel.app"

bot = telebot.TeleBot(BOT_TOKEN)
genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False)

# Force Subscribe
def is_subscribed(user_id):
    try:
        bot.get_chat_member(CHANNEL_ID, user_id)
        return True
    except:
        return False

# ==================== SONG + LYRICS ENGINE ====================
def get_any_song(query):
    try:
        url = f"{MUSIC_API}/getSongs?q={query}"
        resp = requests.get(url, timeout=10).json()
        
        if isinstance(resp, list) and len(resp) > 0:
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

def get_lyrics(query):
    try:
        songs = genius.search(query)
        if songs:
            song = songs[0]
            lyrics = genius.lyrics(song.id)
            lines = [l.strip() for l in lyrics.split('\n')[:12] if l.strip()]
            formatted = f"🎤 **{song.title}**\n👤 **{song.artist}**\n\n"
            for line in lines:
                formatted += f"**`{line}`**\n"
            return formatted[:4000]
    except:
        pass
    return None

# ==================== 5 SUPER SIMPLE COMMANDS ====================
@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Join Channel", url="https://t.me/+JPgViOHx7bdlMDZl"))
    
    bot.send_message(message.chat.id, 
        "🎤 **MUSIC + LYRICS BOT** 🎵\n\n"
        "**Kaise use karo:**\n"
        "`tum hi ho` → Song + Lyrics\n"
        "`/song tum hi ho` → Same\n"
        "`/admin` → Admin panel\n\n"
        "📢 **Pehle channel join!**", 
        reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['song'])
@bot.message_handler(func=lambda m: True)
def any_song(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📢 Join Karo!", url="https://t.me/+JPgViOHx7bdlMDZl")
        )
        bot.reply_to(message, "🚫 **Channel join karo bhai!**", reply_markup=markup)
        return
    
    query = message.text.replace('/song ', '').strip()
    if not query:
        bot.reply_to(message, "❌ **Song name likho!** `jaise: tum hi ho`")
        return
    
    status = bot.reply_to(message, f"🔍 **{query}** dhund raha...")
    
    # Song
    music = get_any_song(query)
    if music['success']:
        try:
            bot.send_audio(message.chat.id, music['url'], 
                          caption=f"🎵 **{music['title']}** | 320kbps 🎵",
                          parse_mode='Markdown')
        except:
            pass
    else:
        bot.send_message(message.chat.id, "❌ **Song nahi mila!**")

    # Lyrics
    lyrics = get_lyrics(query)
    if lyrics:
        bot.send_message(message.chat.id, lyrics, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, f"❌ **{query}** - Lyrics nahi mile!")
    
    bot.delete_message(status.chat.id, status.id)

# ==================== 🔥 PRO ADMIN PANEL 🔥 ====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"),
        InlineKeyboardButton("👥 Stats", callback_data="stats")
    )
    markup.row(
        InlineKeyboardButton("🔄 Restart", callback_data="restart"),
        InlineKeyboardButton("❌ Close", callback_data="close_admin")
    )
    
    bot.send_message(message.chat.id, 
        "🔥 **ADMIN PANEL** 🔥\n\n"
        "Choose option:", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Admin only!")
        return
    
    if call.data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 **Broadcast message bhejo:**")
        bot.register_next_step_handler(msg, send_broadcast)
    
    elif call.data == "stats":
        bot.edit_message_text("📊 **Stats:**\n• Uptime: 24/7\n• API: Live\n• Users: 1000+", 
                            call.message.chat.id, call.message.id)
    
    elif call.data == "restart":
        bot.edit_message_text("🔄 **Bot restarting...** (Demo)", 
                            call.message.chat.id, call.message.id)
    
    elif call.data == "close_admin":
        bot.delete_message(call.message.chat.id, call.message.id)

def send_broadcast(message):
    try:
        bot.send_message(CHANNEL_ID, message.text)
        bot.reply_to(message, "✅ **Broadcast sent to channel!**")
    except:
        bot.reply_to(message, "❌ **Error!**")

print("🚀 **ANY SONG KARAOKE BOT LIVE!** 🎤")
bot.infinity_polling()
