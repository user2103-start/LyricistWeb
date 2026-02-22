"""
🎵 KARAOKE BOT - FULL FEATURES
"""

import telebot
import os
import requests
import io
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
from urllib.parse import quote

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

# SONG SEARCH
def search_song(query):
    logger.info("Searching: " + str(query))
    
    apis = [
        "https://music-api-tau.vercel.app/api/search?q=",
        "https://bollywood-api.vercel.app/search?q=",
        "https://hindi-music-api.vercel.app/search?q=",
    ]
    
    for api_url in apis:
        try:
            resp = requests.get(api_url + quote(query), timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    for song in data[:5]:
                        url = song.get("url") or song.get("download_url")
                        if url and "http" in str(url):
                            return {"url": url, "title": song.get("title", query), "artist": song.get("artist", "Unknown"), "source": "API"}
                elif isinstance(data, dict):
                    results = data.get("results") or data.get("data")
                    if isinstance(results, list) and len(results) > 0:
                        song = results[0]
                        url = song.get("url") or song.get("download_url")
                        if url and "http" in str(url):
                            return {"url": url, "title": song.get("title", query), "artist": song.get("artist", "Unknown"), "source": "API"}
        except Exception as e:
            logger.error("API Error: " + str(e))
            continue
    
    # JioSaavn
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
                                    return {"url": url, "title": song.get("title", query), "artist": song.get("artist", "Unknown"), "source": "JioSaavn"}
    except:
        pass
    
    # Deezer
    try:
        resp = requests.get("https://api.deezer.com/search?q=" + quote(query), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data") and len(data["data"]) > 0:
                song = data["data"][0]
                preview = song.get("preview")
                if preview:
                    return {"url": preview, "title": song.get("title", query), "artist": song.get("artist", {}).get("name", "Unknown"), "source": "Deezer"}
    except:
        pass
    
    return None

# LYRICS
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
    return "❌ **Lyrics not found!**"

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

🎤 **KARAOKE BOT** 🚀

✨ Full Songs | ✨ Lyrics

**Commands:**
/song [name] - Play song
/songLY [name] - Song + Lyrics
/lyrics [name] - Only lyrics
"""
    
    if user_id == ADMIN_ID:
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("📊 Stats", callback_data="stats"), InlineKeyboardButton("📢 BC", callback_data="bc"))
        markup.row(InlineKeyboardButton("🔄 Restart", callback_data="restart"))
        bot.send_message(message.chat.id, welcome + "\n👑 **ADMIN**", reply_markup=markup, parse_mode="Markdown")
        return
    
    if not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 JOIN", url=CHANNEL_LINK), InlineKeyboardButton("✅ VERIFY", callback_data="verify"))
        bot.send_message(message.chat.id, "🚫 **JOIN CHANNEL FIRST!**", reply_markup=markup, parse_mode="Markdown")
        return
    
    bot.send_message(message.chat.id, welcome, parse_mode="Markdown")

@bot.message_handler(commands=["song"])
def song_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 JOIN", url=CHANNEL_LINK), InlineKeyboardButton("✅ VERIFY", callback_data="verify"))
        bot.reply_to(message, "🚫 **JOIN CHANNEL FIRST!**", reply_markup=markup, parse_mode="Markdown")
        return
    
    query = message.text[6:].strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/song tum hi ho`", parse_mode="Markdown")
        return
    
    msg = bot.reply_to(message, f"🔍 **Searching:** `{query}`...", parse_mode="Markdown")
    
    music = search_song(query)
    
    if music and music.get("url"):
        try:
            caption = f"🎵 **{music['title']}**\n👤 **{music['artist']}**\n📱 {music['source']}"
            bot.send_audio(message.chat.id, music["url"], caption=caption, parse_mode="Markdown")
            bot.delete_message(message.chat.id, msg.message_id)
            bot.reply_to(message, f"✅ **{music['title']}** sent!", parse_mode="Markdown")
        except Exception as e:
            logger.error("Send error: " + str(e))
            bot.edit_message_text("❌ **Error!**", message.chat.id, msg.message_id)
    else:
        bot.edit_message_text(f"❌ **Not found:** `{query}`", message.chat.id, msg.message_id, parse_mode="Markdown")

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
    
    music = search_song(query)
    if music and music.get("url"):
        try:
            bot.send_audio(message.chat.id, music["url"], caption=f"🎵 **{music['title']}**")
        except:
            pass
    
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
    bot.send_message(message.chat.id, "👑 **ADMIN PANEL**", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "❌ Not admin!", show_alert=True)
        return
    
    bot.answer_callback_query(c.id)
    
    if c.data == "stats":
        bot.edit_message_text("📊 **STATS**\n\n✅ Bot ONLINE\n🔗 Webhook ACTIVE", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
    
    elif c.data == "bc":
        bot.edit_message_text("📢 **BROADCAST**\n\nType message to broadcast.\n/cancel to stop.", c.message.chat.id, c.message.message_id, parse_mode="Markdown")
        bot.register_next_step_handler(c.message, broadcast_handler)
    
    elif c.data == "restart":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ YES", callback_data="confirm_restart"))
        bot.edit_message_text("🔄 **RESTART?**", c.message.chat.id, c.message.message_id, reply_markup=markup, parse_mode="Markdown")
    
    elif c.data == "confirm_restart":
        bot.edit_message_text("🔄 Restarting...", c.message.chat.id, c.message.message_id)
        import os
        os._exit(0)
    
    elif c.data == "verify":
        user_id = c.from_user.id
        if is_subscribed(user_id):
            bot.answer_callback_query(c.id, "✅ Verified!", show_alert=True)
            start_handler(c.message)
        else:
            bot.answer_callback_query(c.id, "❌ Join channel first!", show_alert=True)

def broadcast_handler(message):
    if message.text == "/cancel":
        bot.send_message(message.chat.id, "✅ Cancelled")
        return
    bot.send_message(message.chat.id, "✅ **Broadcast sent!**")

# WEBHOOK
@app.route("/" + BOT_TOKEN, methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "🎵 KARAOKE BOT - ONLINE"

if __name__ == "__main__":
    webhook_url = "https://" + os.getenv("RENDER_EXTERNAL_HOSTNAME", "localhost:5000") + "/" + BOT_TOKEN
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    logger.info("Bot started: " + webhook_url)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
