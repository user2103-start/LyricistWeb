"""
🎵 KARAOKE BOT - MASTERPIECE EDITION
✅ Admin Panel
✅ Force Subscribe
✅ Any Song Search
✅ Visual Lyrics
✅ Broadcast System
✅ User Stats
"""

import telebot
import asyncio
import aiohttp
import os
import json
import time
import requests
import io
import logging
import datetime
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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ==================== DATA STORAGE ====================
user_stats = {}
song_history = []

# ==================== ASYNC SESSION ====================
async_session = None

def get_async_session():
    global async_session
    if async_session is None:
        async_session = aiohttp.ClientSession()
    return async_session

# ==================== SONG SEARCH APIs ====================
async def search_song_async(query):
    """Search any song using multiple APIs"""
    logger.info("Searching: " + str(query))
    
    session = get_async_session()
    
    apis = [
        {
            "name": "JioSaavn",
            "url": "https://saavn-api.vercel.app/search?q=" + quote(query) + "&limit=3"
        },
        {
            "name": "Deezer", 
            "url": "https://api.deezer.com/search?q=" + quote(query) + "&limit=3"
        },
        {
            "name": "iTunes",
            "url": "https://itunes.apple.com/search?term=" + quote(query) + "&limit=3"
        }
    ]
    
    for api in apis:
        try:
            logger.info("Trying: " + str(api["name"]))
            
            async with session.get(api["url"], timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    try:
                        data = await resp.json()
                        
                        if "deezer" in api["url"]:
                            if data.get("data") and len(data["data"]) > 0:
                                song = data["data"][0]
                                url = song.get("preview")
                                if url:
                                    return {
                                        "url": url,
                                        "title": song.get("title", query),
                                        "artist": song.get("artist", {}).get("name", "Unknown"),
                                        "success": True
                                    }
                        
                        elif "itunes" in api["url"]:
                            if data.get("results") and len(data["results"]) > 0:
                                song = data["results"][0]
                                url = song.get("artworkUrl100")
                                if url:
                                    return {
                                        "url": url.replace("100x100", "600x600"),
                                        "title": song.get("trackName", query),
                                        "artist": song.get("artistName", "Unknown"),
                                        "success": True
                                    }
                        
                        elif "saavn" in api["url"]:
                            if isinstance(data, list) and len(data) > 0:
                                song = data[0]
                                download_url = song.get("downloadUrl")
                                if isinstance(download_url, list) and len(download_url) > 0:
                                    return {
                                        "url": download_url[-1].get("url"),
                                        "title": song.get("title", query),
                                        "artist": song.get("artist", "Unknown"),
                                        "success": True
                                    }
                                    
                    except json.JSONDecodeError:
                        continue
                        
        except asyncio.TimeoutError:
            logger.warning("Timeout: " + str(api["name"]))
            continue
        except Exception as e:
            logger.error("Error " + str(api["name"]) + ": " + str(e))
            continue
    
    return None

# ==================== FALLBACK SYNC SEARCH ====================
def search_song_sync(query):
    """Sync fallback"""
    fallback_apis = [
        "https://music-api-tau.vercel.app/getSongs?q=",
        "https://free-music-api.vercel.app/search?q=",
    ]
    
    for api_url in fallback_apis:
        try:
            resp = requests.get(api_url + quote(query), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    song = data[0]
                    url = song.get("url") or song.get("download_url")
                    if url and "http" in str(url):
                        return {
                            "url": url,
                            "title": song.get("title", query),
                            "artist": song.get("artist", "Unknown"),
                            "success": True
                        }
        except:
            continue
    
    return None

# ==================== GENIUS LYRICS ====================
def get_lyrics(query):
    """Get lyrics from Genius"""
    try:
        import lyricsgenius
        
        genius = lyricsgenius.Genius(
            GENIUS_TOKEN,
            verbose=False,
            timeout=15,
            retries=3
        )
        
        songs = genius.search(query, per_page=5)
        
        if songs and len(songs) > 0:
            for song in songs:
                try:
                    lyrics = genius.lyrics(song.id)
                    
                    if lyrics and len(lyrics) > 100:
                        lines = [l.strip() for l in lyrics.split("\n")
                                if l.strip() and len(l.strip()) > 3][:20]
                        
                        if len(lines) > 5:
                            visual = "🎤 **VISUAL LYRICS** 🎵\n\n"
                            for i, line in enumerate(lines, 1):
                                emoji = "✨" if i % 2 else "🎶"
                                visual = visual + str(emoji) + " `" + str(line) + "`\n"
                            
                            visual = visual + "\n👤 **" + str(song.artist) + "** | 🎵 **" + str(song.title) + "**"
                            return visual
                            
                except:
                    continue
        
    except Exception as e:
        logger.error("Genius error: " + str(e))
    
    return "❌ **Lyrics not found!**\n\nTry English song names for better results."

# ==================== SUBSCRIPTION CHECK ====================
def is_subscribed(user_id):
    """Check if user joined channel"""
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error("Subscribe check error: " + str(e))
        return False

# ==================== UPDATE USER STATS ====================
def update_stats(user_id, username, song_name):
    """Update user statistics"""
    if user_id not in user_stats:
        user_stats[user_id] = {
            "username": username,
            "song_count": 0,
            "songs": []
        }
    
    user_stats[user_id]["song_count"] += 1
    user_stats[user_id]["songs"].append({
        "name": song_name,
        "time": str(datetime.datetime.now())
    })
    
    # Keep only last 10 songs
    if len(user_stats[user_id]["songs"]) > 10:
        user_stats[user_id]["songs"] = user_stats[user_id]["songs"][-10:]

# ==================== COMMANDS ====================
@bot.message_handler(commands=["start"])
def start_handler(message):
    """Start command with welcome message"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    
    welcome = """
🎵 **NAMASTE {name}!** 🙏

🎤 **KARAOKE BOT - MASTERPIECE EDITION** 🚀

✨ **Features:**
- 🎶 **Any Song Search** - Unlimited!
- 📝 **Visual Lyrics** - Synced with song
- ⚡ **Super Fast** - Multiple APIs
- 🎧 **320kbps Quality**

📖 **Commands:**
- `/song [song name]` - Play any song
- `/songLY [song name]` - Song + Lyrics
- `/lyrics [song name]` - Only lyrics

🔥 **Examples:**
`/song tum hi ho`
`/song kesariya`
`/song dilbar`
`/song satranga`
`/song heeriye`
`/song shape of you`
""".format(name=first_name)
    
    # Admin check
    if user_id == ADMIN_ID:
        welcome = welcome + "\n👑 **ADMIN MODE ACTIVE**"
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("📊 Stats", callback_data="admin_stats"))
        markup.row(InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"))
        markup.row(InlineKeyboardButton("👥 Users", callback_data="admin_users"))
        markup.row(InlineKeyboardButton("🔄 Restart", callback_data="admin_restart"))
        bot.send_message(message.chat.id, welcome, reply_markup=markup, parse_mode="Markdown")
        return
    
    # Force subscribe check
    if not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK))
        markup.add(InlineKeyboardButton("✅ VERIFY", callback_data="verify_subscribe"))
        bot.send_message(message.chat.id,
            "🚫 **JOIN CHANNEL FIRST!**\n\n"
            "📢 **Channel:** @your_channel_name\n\n"
            "Bot use karne ke liye channel join karein aur 'VERIFY' button click karein!",
            reply_markup=markup, parse_mode="Markdown", disable_web_page_preview=True)
        return
    
    bot.send_message(message.chat.id, welcome, parse_mode="Markdown")

@bot.message_handler(commands=["song"])
def song_handler(message):
    """Main song command"""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    # Admin check
    is_admin = (user_id == ADMIN_ID)
    
    # Force subscribe check
    if not is_admin and not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK))
        markup.add(InlineKeyboardButton("✅ VERIFY", callback_data="verify_subscribe"))
        bot.reply_to(message,
            "🚫 **JOIN CHANNEL FIRST!**\n\n"
            "Channel join karein aur verify karein!",
            reply_markup=markup, parse_mode="Markdown")
        return
    
    query = message.text[6:].strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/song tum hi ho`\n\nTry: `/song kesariya`", parse_mode="Markdown")
        return
    
    search_msg = bot.reply_to(message, "🔍 **Searching:** `" + str(query) + "`\n\n⏳ Please wait...", parse_mode="Markdown")
    
    # Async search
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        music = loop.run_until_complete(search_song_async(query))
    except Exception as e:
        logger.error("Async error: " + str(e))
        music = None
    finally:
        loop.close()
    
    # Fallback
    if not music or not music.get("url"):
        music = search_song_sync(query)
    
    if music and music.get("url"):
        try:
            caption = "🎵 **" + str(music["title"]) + "**\n👤 **" + str(music["artist"]) + "**\n✨ **320kbps HD** ✅\n\n🔗 Requested by: @" + str(username)
            
            try:
                bot.send_audio(message.chat.id, music["url"], caption=caption, parse_mode="Markdown")
            except:
                resp = requests.get(music["url"], timeout=20)
                if resp.status_code == 200:
                    audio_file = io.BytesIO(resp.content)
                    bot.send_audio(message.chat.id, audio_file, caption=caption, parse_mode="Markdown")
            
            # Update stats
            update_stats(user_id, username, music["title"])
            
            # Add to history
            song_history.append({
                "user": username,
                "song": music["title"],
                "time": str(datetime.datetime.now())
            })
            if len(song_history) > 50:
                song_history.pop(0)
            
            bot.delete_message(message.chat.id, search_msg.message_id)
            success_msg = bot.reply_to(message, "✅ **" + str(music["title"]) + "** sent! 🎶", parse_mode="Markdown")
            
            # Auto delete after 10 seconds
            import threading
            def delete_later():
                time.sleep(10)
                try:
                    bot.delete_message(message.chat.id, success_msg.message_id)
                except:
                    pass
            threading.Thread(target=delete_later).start()
            
        except Exception as e:
            logger.error("Send error: " + str(e))
            bot.edit_message_text(
                "❌ **Error sending song!**\n\nTry another song.",
                message.chat.id, search_msg.message_id, parse_mode="Markdown"
            )
    else:
        bot.edit_message_text(
            "❌ **Song not found!** 😔\n\n🔍 Searched: `" + str(query) + "`\n\n💡 **Tips:**\n• Use exact song name\n• Try: `/song tum hi ho`\n• Try: `/song kesariya`",
            message.chat.id, search_msg.message_id, parse_mode="Markdown"
        )

@bot.message_handler(commands=["songLY"])
def songlyrics_handler(message):
    """Song + Lyrics command"""
    user_id = message.from_user.id
    
    # Admin check
    is_admin = (user_id == ADMIN_ID)
    
    # Force subscribe check
    if not is_admin and not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK))
        markup.add(InlineKeyboardButton("✅ VERIFY", callback_data="verify_subscribe"))
        bot.reply_to(message, "🚫 **JOIN CHANNEL FIRST!**", reply_markup=markup, parse_mode="Markdown")
        return
    
    query = message.text[7:].strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/songLY tum hi ho`", parse_mode="Markdown")
        return
    
    process_msg = bot.reply_to(message, "🎨 **Processing:** `" + str(query) + "`\n\n⏳ Song + Lyrics coming...", parse_mode="Markdown")
    
    # Get song
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        music = loop.run_until_complete(search_song_async(query))
    except:
        music = search_song_sync(query)
    finally:
        loop.close()
    
    # Send song
    if music and music.get("url"):
        try:
            bot.send_audio(message.chat.id, music["url"], caption="🎵 **" + str(music["title"]) + "** - Lyrics below! 👇")
        except:
            pass
    
    # Send lyrics
    lyrics = get_lyrics(query)
    bot.send_message(message.chat.id, lyrics, parse_mode="Markdown")
    bot.delete_message(message.chat.id, process_msg.message_id)

@bot.message_handler(commands=["lyrics"])
def lyrics_handler(message):
    """Only lyrics command"""
    user_id = message.from_user.id
    
    # Admin check
    is_admin = (user_id == ADMIN_ID)
    
    # Force subscribe check
    if not is_admin and not is_subscribed(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK))
        markup.add(InlineKeyboardButton("✅ VERIFY", callback_data="verify_subscribe"))
        bot.reply_to(message, "🚫 **JOIN CHANNEL FIRST!**", reply_markup=markup, parse_mode="Markdown")
        return
    
    query = message.text[8:].strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/lyrics tum hi ho`", parse_mode="Markdown")
        return
    
    lyrics = get_lyrics(query)
    bot.send_message(message.chat.id, lyrics, parse_mode="Markdown")

# ==================== ADMIN PANEL ====================
@bot.message_handler(commands=["admin"])
def admin_handler(message):
    """Admin panel command"""
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📊 Stats", callback_data="admin_stats"))
    markup.row(InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"))
    markup.row(InlineKeyboardButton("👥 Users", callback_data="admin_users"))
    markup.row(InlineKeyboardButton("🎵 History", callback_data="admin_history"))
    markup.row(InlineKeyboardButton("🔄 Restart", callback_data="admin_restart"))
    
    bot.send_message(message.chat.id,
        "👑 **ADMIN PANEL - MASTERPIECE EDITION**\n\n"
        "✅ Bot Status: ONLINE\n"
        "✅ Users Tracked: " + str(len(user_stats)) + "\n"
        "✅ Songs Played: " + str(len(song_history)) + "\n\n"
        "Select an option:",
        reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Handle admin panel callbacks"""
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Not authorized!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id)
    
    if call.data == "admin_stats":
        # Show bot stats
        total_users = len(user_stats)
        total_songs = len(song_history)
        
        stats_text = """
📊 **BOT STATISTICS**

👥 **Total Users:** {users}
🎵 **Total Songs:** {songs}
📅 **Date:** {date}

**Top Users:**
""".format(users=total_users, songs=total_songs, date=str(datetime.datetime.now().strftime("%Y-%m-%d")))
        
        # Top users
        sorted_users = sorted(user_stats.items(), key=lambda x: x[1]["song_count"], reverse=True)[:5]
        for i, (uid, data) in enumerate(sorted_users, 1):
            stats_text = stats_text + str(i) + ". @" + str(data["username"]) + " - " + str(data["song_count"]) + " songs\n"
        
        bot.edit_message_text(stats_text, call.message.chat.id, call.message.id, parse_mode="Markdown")
    
    elif call.data == "admin_broadcast":
        # Start broadcast
        bot.edit_message_text(
            "📢 **BROADCAST MODE**\n\n"
            "Send the message you want to broadcast to all users.\n"
            "Type /cancel to cancel.",
            call.message.chat.id, call.message.id, parse_mode="Markdown"
        )
        bot.register_next_step_handler(call.message, broadcast_message)
    
    elif call.data == "admin_users":
        # Show users list
        users_text = "👥 **USER LIST**\n\n"
        
        sorted_users = sorted(user_stats.items(), key=lambda x: x[1]["song_count"], reverse=True)[:20]
        
        for uid, data in sorted_users:
            users_text = users_text + "• @" + str(data["username"]) + " - " + str(data["song_count"]) + " songs\n"
        
        if len(user_stats) > 20:
            users_text = users_text + "\n... and " + str(len(user_stats) - 20) + " more users"
        
        bot.edit_message_text(users_text, call.message.chat.id, call.message.id, parse_mode="Markdown")
    
    elif call.data == "admin_history":
        # Show song history
        history_text = "🎵 **SONG HISTORY**\n\n"
        
        for item in reversed(song_history[-20:]):
            history_text = history_text + "• " + str(item["song"]) + " - @" + str(item["user"]) + "\n"
        
        bot.edit_message_text(history_text, call.message.chat.id, call.message.id, parse_mode="Markdown")
    
    elif call.data == "admin_broadcast":
        # Start broadcast
        bot.edit_message_text(
            "ðŸ“¢ **BROADCAST MODE**\n\n"
            "Send the message you want to broadcast to all users.\n"
            "Type /cancel to cancel.",
            call.message.chat.id, call.message.id, parse_mode="Markdown"
        )
        bot.register_next_step_handler(call.message, broadcast_message)
    
    elif call.data == "admin_users":
        # Show users list
        users_text = "ðŸ‘¥ **USER LIST**\n\n"
        
        sorted_users = sorted(user_stats.items(), key=lambda x: x[1]["song_count"], reverse=True)[:20]
        
        for uid, data in sorted_users:
            users_text = users_text + "â€¢ @" + str(data["username"]) + " - " + str(data["song_count"]) + " songs\n"
        
        if len(user_stats) > 20:
            users_text = users_text + "\n... and " + str(len(user_stats) - 20) + " more users"
        
        bot.edit_message_text(users_text, call.message.chat.id, call.message.id, parse_mode="Markdown")
    
    elif call.data == "admin_history":
        # Show song history
        history_text = "ðŸŽµ **SONG HISTORY**\n\n"
        
        for item in reversed(song_history[-20:]):
            history_text = history_text + "â€¢ " + str(item["song"]) + " - @" + str(item["user"]) + "\n"
        
        bot.edit_message_text(history_text, call.message.chat.id, call.message.id, parse_mode="Markdown")
    
    elif call.data == "admin_restart":
        # Restart confirmation
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("âœ… YES, RESTART", callback_data="confirm_restart"))
        markup.add(InlineKeyboardButton("âŒ NO", callback_data="cancel_restart"))
        
        bot.edit_message_text(
            "ðŸ”„ **RESTART BOT?**\n\n"
            "Are you sure you want to restart the bot?",
            call.message.chat.id, call.message.id, reply_markup=markup, parse_mode="Markdown"
        )
    
    elif call.data == "confirm_restart":
        bot.edit_message_text("ðŸ”„ **Restarting...**", call.message.chat.id, call.message.id)
        import os
        os._exit(0)
    
    elif call.data == "cancel_restart":
        bot.edit_message_text("âœ… **Restart cancelled**", call.message.chat.id, call.message.id)
    
    elif call.data == "verify_subscribe":
        # Verify subscription
        user_id = call.from_user.id
        
        if is_subscribed(user_id):
            bot.answer_callback_query(call.id, "âœ… Verified! You can now use the bot!", show_alert=True)
            
            welcome = """
ðŸŽµ **NAMASTE!** ðŸ™

ðŸŽ¤ **KARAOKE BOT - MASTERPIECE EDITION** ðŸš€

âœ¨ **Features:**
- ðŸŽ¶ Any Song Search
- ðŸ“ Visual Lyrics
- âš¡ Super Fast
- ðŸŽ§ 320kbps Quality

ðŸ“– **Commands:**
/song [song name]
/songLY [song name]
/lyrics [song name]
"""
            bot.send_message(call.message.chat.id, welcome)
        else:
            bot.answer_callback_query(call.id, "âŒ Please join the channel first!", show_alert=True)

def broadcast_message(message):
    """Handle broadcast message"""
    if message.text == "/cancel":
        bot.send_message(message.chat.id, "âœ… Broadcast cancelled")
        return
    
    # Send to all users who used the bot
    broadcast_count = 0
    for user_id in user_stats.keys():
        try:
            bot.send_message(user_id, "ðŸ“¢ **BROADCAST**\n\n" + str(message.text), parse_mode="Markdown")
            broadcast_count += 1
        except:
            pass
    
    bot.send_message(message.chat.id, "âœ… **Broadcast sent to " + str(broadcast_count) + " users!**")

# ==================== WEBHOOK ====================
@app.route("/" + BOT_TOKEN, methods=["POST"])
def webhook():
    """Webhook handler"""
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    """Health check"""
    return "ðŸŽµ **KARAOKE BOT - MASTERPIECE EDITION**\n\nâœ… Status: ONLINE\nðŸ‘‘ Admin: @your_admin_username"

if __name__ == "__main__":
    # Set webhook
    hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "localhost:5000")
    webhook_url = "https://" + str(hostname) + "/" + str(BOT_TOKEN)
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    
    logger.info("Bot started with webhook: " + str(webhook_url))
    
    # Run with gunicorn
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
