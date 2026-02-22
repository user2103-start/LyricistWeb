"""
KARAOKE BOT - UNLIMITED SONGS
Channel: @your_channel
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
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
from urllib.parse quote

# ==================== CONFIG ====================
BOT_TOKEN = "8454384380:AAH1XIgIJ4qnzvJasPCNgpU7rSlPbiflbRY"
CHANNEL_ID = "-1003751644036"
CHANNEL_LINK = "https://t.me/+JPgViOHx7bdlMDZl"
ADMIN_ID = 6593129349
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

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
    logger.info(f"Searching: {query}")
    
    session = get_async_session()
    
    apis = [
        {
            "name": "JioSaavn",
            "url": f"https://saavn-api.vercel.app/search?q={quote(query)}&limit=3"
        },
        {
            "name": "Deezer", 
            "url": f"https://api.deezer.com/search?q={quote(query)}&limit=3"
        },
        {
            "name": "iTunes",
            "url": f"https://itunes.apple.com/search?term={quote(query)}&limit=3"
        }
    ]
    
    for api in apis:
        try:
            logger.info(f"Trying: {api['name']}")
            
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
            logger.warning(f"Timeout: {api['name']}")
            continue
        except Exception as e:
            logger.error(f"Error {api['name']}: {e}")
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
            resp = requests.get(f"{api_url}{quote(query)}", timeout=10)
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
                            visual = "VISUAL LYRICS\n\n"
                            for i, line in enumerate(lines, 1):
                                emoji = "✨" if i % 2 else "🎶"
                                visual += f"{emoji} {line}\n"
                            
                            visual += f"\n👤 {song.artist} | {song.title}"
                            return visual
                            
                except:
                    continue
        
    except Exception as e:
        logger.error(f"Genius error: {e}")
    
    return "Lyrics not found!"

# ==================== SUBSCRIPTION CHECK ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Subscribe check error: {e}")
        return False

# ==================== COMMANDS ====================
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    welcome = f"""
🎵 NAMASTE {first_name}!

KARAOKE BOT - UNLIMITED EDITION

Features:
- Any Song Search
- Visual Lyrics
- Super Fast
- 320kbps Quality

Commands:
/song [song name] - Play any song
/songLY [song name] - Song + Lyrics
/lyrics [song name] - Only lyrics

Examples:
/song tum hi ho
/song kesariya
/song dilbar
/song satranga
/song heeriye
"""
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, welcome + "\n👑 ADMIN MODE")
        return
    
    if not is_subscribed(user_id):
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("JOIN CHANNEL", url=CHANNEL_LINK)
        )
        bot.send_message(message.chat.id,
            "JOIN CHANNEL FIRST!",
            reply_markup=markup)
        return
    
    bot.send_message(message.chat.id, welcome)

@bot.message_handler(commands=["song"])
def song_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "Join channel first!")
        return
    
    query = message.text[6:].strip()
    if not query:
        bot.reply_to(message, "Usage: /song tum hi ho")
        return
    
    search_msg = bot.reply_to(message, f"Searching: {query}...")
    
    # Async search
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        music = loop.run_until_complete(search_song_async(query))
    except Exception as e:
        logger.error(f"Async error: {e}")
        music = None
    finally:
        loop.close()
    
    # Fallback
    if not music or not music.get("url"):
        music = search_song_sync(query)
    
    if music and music.get("url"):
        try:
            caption = f"{music['title']} - {music['artist']}"
            
            try:
                bot.send_audio(message.chat.id, music["url"], caption=caption)
            except:
                resp = requests.get(music["url"], timeout=20)
                if resp.status_code == 200:
                    audio_file = io.BytesIO(resp.content)
                    bot.send_audio(message.chat.id, audio_file, caption=caption)
            
            bot.delete_message(message.chat.id, search_msg.message_id)
            bot.reply_to(message, f"Sent: {music['title']} 🎶")
            
        except Exception as e:
            logger.error(f"Send error: {e}")
            bot.edit_message_text(
                f"Error sending song!",
                message.chat.id, search_msg.message_id
            )
    else:
        bot.edit_message_text(
            f"Song not found: {query}",
            message.chat.id, search_msg.message_id
        )

@bot.message_handler(commands=["songLY"])
def songlyrics_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "Join channel first!")
        return
    
    query = message.text[7:].strip()
    if not query:
        bot.reply_to(message, "Usage: /songLY tum hi ho")
        return
    
    process_msg = bot.reply_to(message, f"Processing: {query}...")
    
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
            bot.send_audio(message.chat.id, music["url"], caption=f"{music['title']} - Lyrics below!")
        except:
            pass
    
    # Send lyrics
    lyrics = get_lyrics(query)
    bot.send_message(message.chat.id, lyrics)
    bot.delete_message(message.chat.id, process_msg.message_id)

@bot.message_handler(commands=["lyrics"])
def lyrics_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "Join channel first!")
        return
    
    query = message.text[8:].strip()
    if not query:
        bot.reply_to(message, "Usage: /lyrics tum hi ho")
        return
    
    lyrics = get_lyrics(query)
    bot.send_message(message.chat.id, lyrics)

# ==================== WEBHOOK ====================
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "KARAOKE BOT - UNLIMITED EDITION"

if __name__ == "__main__":
    # Set webhook
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost:5000')}/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    
    # Run with gunicorn
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
