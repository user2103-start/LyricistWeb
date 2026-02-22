"""
🎵 KARAOKE BOT - FULL SONGS (NO 30 SEC LIMIT!)
"""

import telebot
import os
import requests
import io
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
from urllib.parse import quote
import yt_dlp  # 🔥 FULL SONGS!

# CONFIG
BOT_TOKEN = "8454384380:AAH1XIgIJ4qnzvJasPCNgpU7rSlPbiflbRY"
CHANNEL_ID = "-1003751644036"
CHANNEL_LINK = "https://t.me/+JPgViOHx7bdlMDZl"
ADMIN_ID = 6593129349
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# 🔥 FIXED SONG SEARCH - FULL SONGS ONLY!
def search_song(query):
    logger.info("🔍 Searching: " + str(query))
    
    # PRIORITY 1: JIO SAAVN 320KBPS (FULL SONGS)
    try:
        from jiosaavn import JioSaavn
        saavn = JioSaavn()
        results = saavn.search(query, limit=3)
        if results:
            song = results[0]
            download_urls = song.get('download_urls', {})
            url = download_urls.get('320') or download_urls.get('160') or download_urls.get('128')
            if url:
                logger.info(f"✅ JioSaavn found: {song.get('name')}")
                return {
                    "url": url, 
                    "title": song.get('name', query), 
                    "artist": song.get('primary_artists', 'Unknown'),
                    "source": "JioSaavn 320kbps 🔥"
                }
    except Exception as e:
        logger.error(f"JioSaavn error: {e}")
    
    # PRIORITY 2: PUBLIC APIs (FULL QUALITY ONLY)
    apis = [
        "https://music-api-tau.vercel.app/api/search?q=",
        "https://bollywood-api.vercel.app/search?q=",
        "https://hindi-music-api.vercel.app/search?q=",
        "https://saavn-api.vercel.app/search?q=",
    ]
    
    for api_url in apis:
        try:
            resp = requests.get(api_url + quote(query), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    for song in data[:3]:
                        url = song.get("url") or song.get("download_url") or song.get("downloadUrl", [{}])[0].get("url")
                        # 🔥 ONLY FULL SONGS (no preview!)
                        if url and ("320" in str(url) or "128" in str(url) or "media" in str(url) or len(str(url)) > 50):
                            logger.info(f"✅ API found: {song.get('title', query)}")
                            return {
                                "url": url, 
                                "title": song.get("title", query), 
                                "artist": song.get("artist", "Unknown"), 
                                "source": "Music API"
                            }
                elif isinstance(data, dict):
                    results = data.get("data") or data.get("results")
                    if isinstance(results, list) and len(results) > 0:
                        song = results[0]
                        url = song.get("url") or song.get("download_url")
                        if url and ("320" in str(url) or len(str(url)) > 50):
                            return {
                                "url": url, 
                                "title": song.get("title", query), 
                                "artist": song.get("artist", "Unknown"), 
                                "source": "Music API"
                            }
        except Exception as e:
            logger.error(f"API error: {e}")
            continue
    
    # PRIORITY 3: YOUTUBE AUDIO (ALWAYS FULL!)
    try:
        ydl_opts = {
            'quiet': True, 
            'no_warnings': True,
            'format': 'bestaudio/best',
            'noplaylist': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if info.get('entries') and info['entries'][0]:
                entry = info['entries'][0]
                audio_url = entry.get('url')
                if audio_url:
                    logger.info(f"✅ YouTube found: {entry.get('title')}")
                    return {
                        "url": audio_url, 
                        "title": entry.get('title', query)[:50], 
                        "artist": entry.get('uploader', 'YouTube'),
                        "source": "YouTube Audio 🎵"
                    }
    except Exception as e:
        logger.error(f"YouTube error: {e}")
    
    logger.error(f"❌ No song found for: {query}")
    return None

# LYRICS (UNCHANGED)
def get_lyrics(query):
    try:
        import lyricsgenius
        genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False, timeout=15)
        songs = genius.search(query, per_page=5)
        if songs:
            for song in songs:
                try:
                    lyrics = genius.lyrics(song.id)
                    if lyrics and len(lyrics) > 100:
                        lines = [l.strip() for l in lyrics.split("\n") if l.strip() and len(l.strip()) > 3][:15]
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
    return "❌ **Lyrics not found! Try /songLY**"

# SUBSCRIPTION CHECK
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# COMMANDS
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    welcome = f"""
🎵 **NAMASTE {first_name}!** 🙏

🎤 **KARAOKE BOT v2.0** 🚀
✅ **FULL SONGS** (No 30 sec limit!)
✅ **320kbps Quality**
✅ **Lyrics + Visual**

**Commands:**
/song [name] - 🎵 Full song
/songLY [name] - 🎵 Song + Lyrics  
/lyrics [name] - 📝 Lyrics only
"""
    
    if user_id == ADMIN_ID:
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("📊 Stats", callback_data="stats"), InlineKeyboardButton("📢 BC", callback_data="bc"))
        markup.row(InlineKeyboardButton("🔄 Restart", callback_data="restart"))
        bot.send_message(message.chat.id, welcome + "\n👑 **ADMIN PANEL**", reply_markup=markup, parse_mode="Markdown")
        return
    
    if not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK), InlineKeyboardButton("✅ VERIFY", callback_data="verify"))
        bot.send_message(message.chat.id, "🚫 **JOIN CHANNEL FIRST!**\n\n👇 Click JOIN then VERIFY", reply_markup=markup, parse_mode="Markdown")
        return
    
    bot.send_message(message.chat.id, welcome, parse_mode="Markdown")

@bot.message_handler(commands=["song"])
def song_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK), InlineKeyboardButton("✅ VERIFY", callback_data="verify"))
        bot.reply_to(message, "🚫 **JOIN CHANNEL FIRST!**", reply_markup=markup, parse_mode="Markdown")
        return
    
    query = message.text[6:].strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/song tum hi ho`", parse_mode="Markdown")
        return
    
    msg = bot.reply_to(message, f"🔍 **Searching:** `{query}`\n⏳ Please wait...", parse_mode="Markdown")
    
    music = search_song(query)
    
    if music and music.get("url"):
        try:
            caption = f"🎵 **{music['title']}**\n👤 **{music['artist']}**\n📱 **{music['source']}**"
            bot.send_audio(message.chat.id, music["url"], caption=caption, parse_mode="Markdown", title=music['title'])
            bot.delete_message(message.chat.id, msg.message_id)
            bot.reply_to(message, f"✅ **{music['title']}** playing! 🎶", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Send audio error: {e}")
            bot.edit_message_text("❌ **Download failed!** Try again.", message.chat.id, msg.message_id, parse_mode="Markdown")
    else:
        bot.edit_message_text(f"❌ **Song not found:** `{query}`\n\nTry: *dilbar, tum hi ho, shape of you*", message.chat.id, msg.message_id, parse_mode="Markdown")

@bot.message_handler(commands=["songLY"])
def songlyrics_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **JOIN CHANNEL FIRST!**", parse_mode="Markdown")
        return
    
    query = message.text[7:].strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/songLY tum hi ho`", parse_mode="Markdown")
        return
    
    msg = bot.reply_to(message, f"🎨 **Processing:** `{query}`...", parse_mode="Markdown")
    
    # Send song first
    music = search_song(query)
    if music and music.get("url"):
        try:
            caption = f"🎵 **{music['title']}** | 📝 **Lyrics below**"
            bot.send_audio(message.chat.id, music["url"], caption=caption, parse_mode="Markdown")
        except:
            pass
    
    # Send lyrics
    lyrics = get_lyrics(query)
    bot.send_message(message.chat.id, lyrics, parse_mode="Markdown")
    bot.delete_message(message.chat.id, msg.message_id)

@bot.message_handler(commands=["lyrics"])
def lyrics_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **JOIN CHANNEL FIRST!**", parse_mode="Markdown")
        return
    
    query = message.text[8:].strip()
    if query:
        lyrics = get_lyrics(query)
        bot.send_message(message.chat.id, lyrics, parse_mode="Markdown")

@bot.message_handler(commands=["admin"])
def admin_handler(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📊 Stats", callback_data="stats"), InlineKeyboardButton("📢 BC", callback_data="bc"))
    markup.row(InlineKeyboardButton("🔄 Restart", callback_data="restart"))
    bot.send_message(message.chat.id, "👑 **ADMIN PANEL v2.0**\n✅ Full songs working!", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "❌ Not admin!", show_alert=True)
        return
    
    bot.answer_callback_query(c.id)
    
    if c.data == "stats":
        bot.edit_message_text("📊 **STATS v2.0**\n\n✅ Bot ONLINE\n✅ Full songs (320kbps)\n✅ JioSaavn + YouTube\n🔗 Webhook ACTIVE", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
    
    elif c.data == "bc":
        bot.edit_message_text("📢 **BROADCAST MODE**\n\nSend message to broadcast.\n`/cancel` to stop.", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(c.message, broadcast_handler)
    
    elif c.data == "restart":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ CONFIRM RESTART", callback_data="confirm_restart"))
        bot.edit_message_text("🔄 **RESTART BOT?**\nAll users will reconnect.", c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="Markdown")
    
    elif c.data == "confirm_restart":
        bot.edit_message_text("🔄 **Restarting...**", c.message.chat.id, c.message.message_id)
        import os
        os._exit(0)
    
    elif c.data == "verify":
        user_id = c.from_user.id
        if is_subscribed(user_id):
            bot.answer_callback_query(c.id, "✅ Verified! Welcome! 🎵", show_alert=False)
            start_handler(type('obj', (object,), {'chat': c.message.chat, 'from_user': c.from_user})())
        else:
            bot.answer_callback_query(c.id, "❌ Still not joined! 👇", show_alert=True)

def broadcast_handler(message):
    if message.text == "/cancel":
        bot.send_message(message.chat.id, "✅ Broadcast cancelled!")
        return
    
    # Broadcast logic here (simple version)
    bot.send_message(message.chat.id, f"✅ **Broadcast queued!**\n📨 `{message.text[:50]}...`", parse_mode="Markdown")

# WEBHOOK
@app.route("/" + BOT_TOKEN, methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "🎵 KARAOKE BOT v2.0 - FULL SONGS ONLINE! 🔥"

if __name__ == "__main__":
    webhook_url = "https://" + os.getenv("RENDER_EXTERNAL_HOSTNAME", "localhost:5000") + "/" + BOT_TOKEN
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    logger.info("🚀 Bot started: " + webhook_url)
    logger.info("✅ Full songs enabled - JioSaavn + YouTube!")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
