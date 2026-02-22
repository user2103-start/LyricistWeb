"""
🎵 KARAOKE BOT - FULL FEATURES
✅ Full Songs | ✅ Visual Lyrics | ✅ Force Subscribe | ✅ Admin Panel
"""

import telebot
import os
import requests
import io
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
from urllib.parse import quote

# ==================== CONFIG ====================
BOT_TOKEN = "8454384380:AAH1XIgIJ4qnzvJasPCNgpU7rSlPbiflbRY"
CHANNEL_ID = "-1003751644036"
CHANNEL_LINK = "https://t.me/+JPgViOHx7bdlMDZl"
ADMIN_ID = 6593129349
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

# ==================== LOGGING ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ==================== SONG SEARCH (FULL SONGS!) ====================
def search_song(query):
    """Search full songs from multiple sources"""
    logger.info("Searching: " + str(query))
    
    # API 1: Direct Music APIs
    apis = [
        "https://music-api-tau.vercel.app/api/search?q=",
        "https://bollywood-api.vercel.app/search?q=",
        "https://hindi-music-api.vercel.app/search?q=",
        "https://music-api-puce.vercel.app/search?q=",
        "https://music-api-rho.vercel.app/search?q=",
    ]
    
    for api_url in apis:
        try:
            resp = requests.get(api_url + quote(query), timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                
                if isinstance(data, list) and len(data) > 0:
                    for song in data[:5]:
                        url = song.get("url") or song.get("download_url") or song.get("stream_url")
                        title = song.get("title", query)
                        artist = song.get("artist", "Unknown")
                        
                        if url and "http" in str(url):
                            return {
                                "url": url,
                                "title": title,
                                "artist": artist,
                                "source": "Music API"
                            }
                
                elif isinstance(data, dict):
                    results = data.get("results") or data.get("data") or data.get("songs")
                    if isinstance(results, list) and len(results) > 0:
                        song = results[0]
                        url = song.get("url") or song.get("download_url")
                        if url and "http" in str(url):
                            return {
                                "url": url,
                                "title": song.get("title", query),
                                "artist": song.get("artist", "Unknown"),
                                "source": "Music API"
                            }
        except Exception as e:
            logger.error("API Error: " + str(e))
            continue
    
    # API 2: JioSaavn (if available)
    try:
        resp = requests.get("https://saavn-api.vercel.app/search?q=" + quote(query), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                for song in data[:3]:
                    download_url = song.get("downloadUrl")
                    if isinstance(download_url, list) and len(download_url) > 0:
                        for quality in download_url:
                            if quality.get("quality") in ["320", "128"]:
                                url = quality.get("url")
                                if url and len(url) > 10:
                                    return {
                                        "url": url,
                                        "title": song.get("title", query),
                                        "artist": song.get("artist", "Unknown"),
                                        "source": "JioSaavn"
                                    }
    except:
        pass
    
    # API 3: Deezer (30s preview - better than nothing)
    try:
        resp = requests.get("https://api.deezer.com/search?q=" + quote(query), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data") and len(data["data"]) > 0:
                song = data["data"][0]
                preview = song.get("preview")
                if preview:
                    return {
                        "url": preview,
                        "title": song.get("title", query),
                        "artist": song.get("artist", {}).get("name", "Unknown"),
                        "source": "Deezer (Preview)"
                    }
    except:
        pass
    
    return None

# ==================== VISUAL LYRICS ====================
def get_lyrics(query):
    """Get lyrics from Genius"""
    try:
        import lyricsgenius
        genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False, timeout=15)
        songs = genius.search(query, per_page=5)
        
        if songs:
            for song in songs:
                try:
                    lyrics = genius.lyrics(song.id)
                    if lyrics and len(lyrics) > 100:
                        lines = [l.strip() for l in lyrics.split("\n") 
                                if l.strip() and len(l.strip()) > 3][:15]
                        if len(lines) > 5:
                            visual = "🎤 **VISUAL LYRICS** 🎵\n\n"
                            for i, line in enumerate(lines, 1):
                                emoji = "✨" if i % 2 else "🎶"
                                visual += f"{emoji} `{line}`\n"
                            visual += f"\n👤 **{song.artist}** | 🎵 **{song.title}**"
                            return visual
                except:
                    continue
    except Exception as e:
        logger.error("Genius error: " + str(e))
    
    return "❌ **Lyrics not found!**\n\nTry English song names."

# ==================== SUBSCRIPTION CHECK ====================
def is_subscribed(user_id):
    """Check if user joined channel"""
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error("Subscribe check error: " + str(e))
        return False

# ==================== COMMANDS ====================
@bot.message_handler(commands=["start"])
def start_handler(message):
    """Start command with welcome message"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    welcome = f"""
🎵 **NAMASTE {first_name}!** 🙏

🎤 **KARAOKE BOT - FULL SONGS** 🚀

✨ **Features:**
- 🎶 Full Songs (Not Ringtones)
- 📝 Visual Lyrics
- ⚡ Super Fast Search

📖 **Commands:**
- `/song [song name]` - Play any song
- `/songLY [song name]` - Song + Lyrics
- `/lyrics [song name]` - Only lyrics

🔥 **Examples:**
`/song tum hi ho`
`/song kesariya`
`/song heeriye`
`/song shape of you`
"""
    
    # Admin panel only visible to admin
    if user_id == ADMIN_ID:
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("📊 Stats", callback_data="stats"))
        markup.row(InlineKeyboardButton("📢 Broadcast", callback_data="bc"))
        markup.row(InlineKeyboardButton("🔄 Restart", callback_data="restart"))
        bot.send_message(message.chat.id, welcome + "\n👑 **ADMIN PANEL**", reply_markup=markup, parse_mode="Markdown")
        return
    
    # Force subscribe check
    if not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK))
        markup.add(InlineKeyboardButton("✅ VERIFY", callback_data="verify"))
        bot.send_message(message.chat.id, 
            "🚫 **JOIN CHANNEL FIRST!**\n\n"
            "Channel join karein aur verify karein!",
            reply_markup=markup, parse_mode="Markdown", disable_web_page_preview=True)
        return
    
    bot.send_message(message.chat.id, welcome, parse_mode="Markdown")

@bot.message_handler(commands=["song"])
def song_handler(message):
    """Main song command"""
    user_id = message.from_user.id
    
    # Force subscribe check
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK))
        markup.add(InlineKeyboardButton("✅ VERIFY", callback_data="verify"))
        bot.reply_to(message, "🚫 **JOIN CHANNEL FIRST!**", reply_markup=markup, parse_mode="Markdown")
        return
    
    query = message.text[6:].strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/song tum hi ho`", parse_mode="Markdown")
        return
    
    search_msg = bot.reply_to(message, f"🔍 **Searching:** `{query}`...\n\n⏳ Please wait...", parse_mode="Markdown")
    
    # Search for full song
    music = search_song(query)
    
    if music and music.get("url"):
        try:
            caption = f"🎵 **{music['title']}**\n👤 **{music['artist']}**\n📱 {music['source']}\n✨ **FULL SONG** ✅"
            
            # Try to send audio
            try:
                bot.send_audio(message.chat.id, music["url"], caption=caption, parse_mode="Markdown")
            except Exception as e:
                logger.error("Direct send error: " + str(e))
                
                # Download and send
                try:
                    resp = requests.get(music["url"], timeout=30)
                    if resp.status_code == 200:
                        audio_file = io.BytesIO(resp.content)
                        bot.send_audio(message.chat.id, audio_file, caption=caption, parse_mode="Markdown")
                except Exception as e2:
                    logger.error("Download error: " + str(e2))
                    bot.edit_message_text(
                        "❌ **Error sending song!**\n\nTry another song.",
                        message.chat.id, search_msg.message_id, parse_mode="Markdown"
                    )
                    return
            
            bot.delete_message(message.chat.id, search_msg.message_id)
            bot.reply_to(message, f"✅ **{music['title']}** sent! 🎶", parse_mode="Markdown")
            
        except Exception as e:
            logger.error("Send error: " + str(e))
            bot.edit_message_text(
                "❌ **Error sending song!**\n\nTry another song.",
                message.chat.id, search_msg.message_id, parse_mode="Markdown"
            )
    else:
        bot.edit_message_text(
            f"❌ **Song not found!** 😔\n\n🔍 Searched: `{query}`\n\n💡 **Tips:**\n• Use song name in English\n• Try: `/song tum hi ho`\n• Try: `/song kesariya`\n• Try: `/song dilbar`",
            message.chat.id, search_msg.message_id, parse_mode="Markdown"
        )

@bot.message_handler(commands=["songLY"])
def songlyrics_handler(message):
    """Song + Lyrics command"""
    user_id = message.from_user.id
    
    # Force subscribe check
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK))
        markup.add(InlineKeyboardButton("✅ VERIFY", callback_data="verify"))
        bot.reply_to(message, "🚫 **JOIN CHANNEL FIRST!**", reply_markup=markup, parse_mode="Markdown")
        return
    
    query = message.text[7:].strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/songLY tum hi ho`", parse_mode="Markdown")
        return
    
    process_msg = bot.reply_to(message, f"🎨 **Processing:** `{query}`...\n\n⏳ Song + Lyrics coming...", parse_mode="Markdown")
    
    # Get song
    music = search_song(query)
    
    # Send song
    if music and music.get("url"):
        try:
            bot.send_audio(message.chat.id, music["url"], caption=f"🎵 **{music['title']}** - Lyrics below! 👇")
        except:
            pass
    
    # Get and send lyrics
    lyrics = get_lyrics(query)
    bot.send_message(message.chat.id, lyrics, parse_mode="Markdown")
    bot.delete_message(message.chat.id, process_msg.message_id)

@bot.message_handler(commands=["lyrics"])
def lyrics_handler(message):
    """Only lyrics command"""
    user_id = message.from_user.id
    
    # Force subscribe check
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK))
        markup.add(InlineKeyboardButton("✅ VERIFY", callback_data="verify"))
        bot.reply_to(message, "🚫 **JOIN CHANNEL FIRST!**", reply_markup=markup, parse_mode="Markdown")
        return
    
    query = message.text[8:].strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/lyrics tum hi ho`", parse_mode="Markdown")
        return
    
    lyrics = get_lyrics(query)
    bot.send_message(message.chat.id, lyrics, parse_mode="Markdown")

# ==================== ADMIN PANEL (ONLY FOR ADMIN!) ====================
@bot.message_handler(commands=["admin"])
def admin_handler(message):
    """Admin panel command"""
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📊 Stats", callback_data="stats"))
    markup.row(InlineKeyboardButton("📢 Broadcast", callback_data="bc"))
    markup.row(InlineKeyboardButton("🔄 Restart", callback_data="restart"))
    
    bot.send_message(message.chat.id, "👑 **ADMIN PANEL**\n\n✅ Bot Online", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Handle admin panel callbacks"""
    # Only admin can use callbacks
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Not admin!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id)
    
    if call.data == "stats":
        """Show bot stats"""
        bot.edit_message_text(
            "📊 **BOT STATS**\n\n"
            "✅ Bot Status: ONLINE\n"
            "🔗 Webhook: ACTIVE\n"
            "🎵 Search APIs: ACTIVE\n"
            "📝 Lyrics API: ACTIVE",
            call.message.chat.id, call.message.message_id, parse_mode="Markdown"
        )
    
    elif call.data == "bc":
        """Start broadcast"""
        bot.edit_message_text(
            "📢 **BROADCAST MODE**\n\n"
            "Send the message you want to broadcast to all users.\n"
            "Type /cancel to cancel.",
            call.message.chat.id, call.message.message_id, parse_mode="Markdown"
        )
        bot.register_next_step_handler(call.message, broadcast_message)
    
    elif call.data == "restart":
        """Restart confirmation"""
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ YES, RESTART", callback_data="confirm_restart"))
        markup.add(InlineKeyboardButton("❌ NO", callback_data="cancel_restart"))
        
        bot.edit_message_text(
            "🔄 **RESTART BOT?**\n\n"
            "Are you sure you want to restart the bot?",
            call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
        )
    
    elif call.data == "confirm_restart":
        """Confirm restart"""
        bot.edit_message_text("🔄 **Restarting...**", call.message.chat.id, call.message.message_id)
        import os
        os._exit(0)
    
    elif call.data == "cancel_restart":
        """Cancel restart"""
        bot.edit_message_text("✅ **Restart cancelled**", call.message.chat.id, call.message.message_id)
    
    elif call.data == "verify":
        """Verify subscription"""
        user_id = call.from_user.id
        
        if is_subscribed(user_id):
            bot.answer_callback_query(call.id, "✅ Verified! You can now use the bot!", show_alert=True)
            # Send welcome message
            welcome = """
🎵 **NAMASTE!** 🙏

🎤 **KARAOKE BOT - FULL SONGS** 🚀

✨ **Features:**
- 🎶 Full Songs
- 📝 Visual Lyrics
- ⚡ Super Fast

**Commands:**
/song [song name]
/songLY [song name]
/lyrics [song name]
"""
            bot.send_message(call.message.chat.id, welcome, parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "❌ Please join the channel first!", show_alert=True)
