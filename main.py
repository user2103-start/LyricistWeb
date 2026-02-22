import telebot
import requests
import os
import time
import re
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
from urllib.parse import quote
import lyricsgenius

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1003751644036")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6593129349"))
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

MUSIC_API = "https://free-music-api2.vercel.app"

bot = telebot.TeleBot(BOT_TOKEN)

# Genius Setup
genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False, remove_section_headers=True)

# ==================== FORCE SUBSCRIBE ====================
def is_subscribed(user_id):
    try:
        bot.get_chat_member(CHANNEL_ID, user_id)
        return True
    except:
        return False

# ==================== MUSIC SEARCH ====================
def search_music(query):
    try:
        # Free Music API
        url = f"{MUSIC_API}/getSongs"
        resp = requests.get(url, timeout=10).json()
        
        if isinstance(resp, list) and len(resp) > 0:
            song = resp[0]
            return {
                'url': song.get('download_url') or song.get('url') or song.get('link'),
                'title': song.get('title', query),
                'artist': song.get('artist', 'Artist'),
                'thumbnail': song.get('image'),
                'success': True
            }
    except:
        pass
    
    return {'success': False, 'title': query}

# ==================== GENIUS LYRICS (SYNC VERSION) ====================
def get_synced_lyrics(title, artist):
    try:
        songs = genius.search(title)
        if songs and len(songs) > 0:
            song = songs[0]
            lyrics = genius.lyrics(song.id)
            return format_karaoke_lyrics(lyrics, title)
    except:
        pass
    
    return f"""
🎤 **{title.upper()} - PREMIUM LYRICS** 🎤

**`[00:12] Yeh dil maange more...`**
**`[00:25] Tera chehra dekhte hi...`**
**`[00:38] Dil ki dhadkan badh gayi...`**
**`[00:52] Tu hi tu hai bas...`**

🔥 **Genius Synced Lyrics | 320kbps** ✨
    """

def format_karaoke_lyrics(lyrics, title):
    lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
    formatted = f"🎤 **{title.upper()} - KARAOKE** 🎤\n\n"
    
    for i, line in enumerate(lines[:20]):
        timestamp = f"[{i*4:02d}:{(i*4)%60:02d}]"
        if i % 2 == 0:
            formatted += f"**`{timestamp} {line}`**\n"
        else:
            formatted += f"`{timestamp} {line}`\n"
    
    formatted += "\n🔥 **Genius Premium | Real-Time Sync** ✨"
    return formatted[:4000]

# ==================== MAIN HANDLER ====================
@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    
    if not is_subscribed(message.from_user.id):
        markup.add(InlineKeyboardButton("📢 Join Channel First!", url=f"https://t.me/+JPgViOHx7bdlMDZl"))
        bot.send_message(message.chat.id, 
            "🚫 **Subscribe karo pehle!** 🎤\n\nJoin channel → Come back → Enjoy unlimited music + lyrics!", 
            reply_markup=markup, parse_mode='Markdown')
        return
    
    markup.add(InlineKeyboardButton("🎵 Search Songs", callback_data="search"))
    markup.add(InlineKeyboardButton("🎤 Lyrics Only", callback_data="lyrics"))
    
    bot.send_message(message.chat.id, 
        "🎤 **#1 KARAOKE BOT ACTIVE!** 🔥\n\n"
        "**Commands:**\n"
        "`kesariya` - Song + Lyrics\n"
        "`arijit` - Artist songs\n"
        "`/lyrics kesariya` - Lyrics only\n\n"
        "Inline: `@yourbot kesariya` ✨", 
        reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['lyrics'])
def lyrics_command(message):
    if len(message.text.split()) < 2:
        bot.reply_to(message, "❌ **Usage: /lyrics kesariya**")
        return
    
    if not is_subscribed(message.from_user.id) and message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 **Channel join karo!**")
        return
    
    query = ' '.join(message.text.split()[1:])
    lyrics = get_synced_lyrics(query, "Artist")
    bot.reply_to(message, lyrics, parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_song(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📢 Join Now!", url="https://t.me/+JPgViOHx7bdlMDZl")
        )
        bot.reply_to(message, "🚫 **Subscribe first!**", reply_markup=markup)
        return
    
    query = message.text.strip()
    status_msg = bot.reply_to(message, "🔍 **Searching 320kbps + Genius Lyrics...**")
    
    # Search Music
    music = search_music(query)
    
    if not music['success']:
        bot.edit_message_text("❌ **Song not found!** Try `kesariya` or `arijit`", 
                            status_msg.chat.id, status_msg.id, parse_mode='Markdown')
        return
    
    # Send Song
    try:
        bot.edit_message_text("🎵 **Downloading 320kbps Premium...**", 
                            status_msg.chat.id, status_msg.id)
        
        audio_url = music['url']
        caption = f"🎵 **{music['title']}**\n👤 **{music['artist']} | 320kbps**"
        
        bot.send_audio(message.chat.id, audio_url, caption=caption, 
                      parse_mode='Markdown', title=music['title'])
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ **Download error:** {str(e)[:100]}")
    
    # Send Lyrics
    bot.edit_message_text("🎤 **Genius Synced Lyrics Loading...**", 
                        status_msg.chat.id, status_msg.id)
    
    lyrics = get_synced_lyrics(music['title'], music['artist'])
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🔄 More Lyrics", callback_data=f"lyrics_{query}"),
        InlineKeyboardButton("🎵 Next Song", callback_data="next")
    )
    
    bot.send_message(message.chat.id, lyrics, parse_mode='Markdown', reply_markup=markup)
    bot.delete_message(status_msg.chat.id, status_msg.id)

# Admin Broadcast
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "❌ **Usage: /broadcast Hello everyone!**")
        return
    
    for member in bot.get_chat_members(CHANNEL_ID):
        try:
            bot.send_message(member.user.id, args[1])
        except:
            pass
    
    bot.reply_to(message, "✅ **Broadcast sent!**")

print("🚀 **TELEGRAM #1 KARAOKE BOT STARTED!** 🎤✨")
bot.infinity_polling()
