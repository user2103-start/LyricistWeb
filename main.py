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
from urllib.parse import quote

# ==================== CONFIG ====================
# Set these in Render Environment Variables!
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Your Telegram Bot Token
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1003751644036")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/+JPgViOHx7bdlMDZl")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6593129349"))
GENIUS_TOKEN = os.getenv("GENIUS_TOKEN")  # Genius API Token

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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

# ==================== UNLIMITED SONG SEARCH APIs ====================
# Ye APIs kisi bhi song ko search kar sakte hain - unlimited!

SONG_APIS = [
    {
        "name": "JioSaavn API",
        "url": "https://saavn-api.vercel.app/search?q=",
        "format": lambda data: {
            'url': data['downloadUrl'][-1]['url'] if isinstance(data.get('downloadUrl'), list) else data.get('downloadUrl'),
            'title': data.get('title', 'Unknown'),
            'artist': ', '.join([a['name'] for a in data.get('artists', {}).get('primary', [])]) or 'Unknown',
            'image': data.get('image', ''),
            'success': True
        }
    },
    {
        "name": "Music API 1",
        "url": "https://music-api-tau.vercel.app/api/search?q=",
        "format": lambda data: {
            'url': data.get('url') or data.get('download_url') or data.get('link'),
            'title': data.get('title', 'Unknown'),
            'artist': data.get('artist', 'Unknown'),
            'image': data.get('image', ''),
            'success': True
        }
    },
    {
        "name": "Deezer API",
        "url": "https://api.deezer.com/search?q=",
        "format": lambda data: {
            'url': data.get('preview'),
            'title': data.get('title', 'Unknown'),
            'artist': data.get('artist', {}).get('name', 'Unknown') if isinstance(data.get('artist'), dict) else str(data.get('artist')),
            'image': data.get('album', {}).get('cover_medium', '') if isinstance(data.get('album'), dict) else '',
            'success': True
        }
    },
    {
        "name": "iTunes API",
        "url": "https://itunes.apple.com/search?term=",
        "format": lambda data: {
            'url': data.get('artworkUrl100').replace('100x100', '600x600') if data.get('artworkUrl100') else None,
            'title': data.get('trackName', 'Unknown'),
            'artist': data.get('artistName', 'Unknown'),
            'image': data.get('artworkUrl100', ''),
            'success': True
        }
    }
]

async def search_song_async(query):
    """Search ANY song using multiple APIs"""
    logger.info(f"🔍 Searching: {query}")
    
    session = get_async_session()
    
    for api in SONG_APIS:
        try:
            # Clean query
            clean_query = quote(query.strip())
            url = f"{api['url']}{clean_query}&limit=3"
            
            logger.info(f"📡 Trying: {api['name']}")
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status == 200:
                    try:
                        data = await resp.json()
                        
                        # Handle different API response formats
                        if "deezer" in api['url']:
                            if data.get('data') and len(data['data']) > 0:
                                result = api['format'](data['data'][0])
                                if result.get('url'):
                                    logger.info(f"✅ Found on: {api['name']}")
                                    return result
                        
                        elif "itunes" in api['url']:
                            if data.get('results') and len(data['results']) > 0:
                                result = api['format'](data['results'][0])
                                if result.get('url'):
                                    logger.info(f"✅ Found on: {api['name']}")
                                    return result
                        
                        elif isinstance(data, list) and len(data) > 0:
                            result = api['format'](data[0])
                            if result.get('url') and 'http' in str(result['url']):
                                logger.info(f"✅ Found on: {api['name']}")
                                return result
                        
                        elif isinstance(data, dict) and data.get('results'):
                            result = api['format'](data['results'][0])
                            if result.get('url'):
                                logger.info(f"✅ Found on: {api['name']}")
                                return result
                                
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        logger.error(f"Parse error ({api['name']}): {e}")
                        continue
                        
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Timeout: {api['name']}")
            continue
        except Exception as e:
            logger.error(f"❌ Error ({api['name']}): {e}")
            continue
    
    logger.error(f"❌ No song found: {query}")
    return None

# ==================== FALLBACK: DIRECT DOWNLOAD APIs ====================
def search_song_sync(query):
    """Sync fallback for when async fails"""
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
                    url = song.get('url') or song.get('download_url') or song.get('link')
                    if url and 'http' in str(url):
                        return {
                            'url': url,
                            'title': song.get('title', query),
                            'artist': song.get('artist', 'Unknown'),
                            'success': True
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
        
        # Search for song
        songs = genius.search(query, per_page=5)
        
        if songs and len(songs) > 0:
            # Try to find best match
            for song in songs:
                try:
                    # Get lyrics
                    lyrics = genius.lyrics(song.id)
                    
                    if lyrics and len(lyrics) > 100:
                        # Format lyrics
                        lines = [l.strip() for l in lyrics.split('\n') 
                                if l.strip() and len(l.strip()) > 3][:20]
                        
                        if len(lines) > 5:
                            visual = "🎤 **VISUAL LYRICS** 🎵\n\n"
                            for i, line in enumerate(lines, 1):
                                emoji = "✨" if i % 2 else "🎶"
                                visual += f"{emoji} `{line}`\n"
                            
                            visual += f"\n👤 **{song.artist}** | 🎵 **{song.title}**"
                            return visual
                            
                except Exception as e:
                    logger.error(f"Lyrics error: {e}")
                    continue
        
    except Exception as e:
        logger.error(f"Genius API error: {e}")
    
    return "❌ **Lyrics not found!**\n\nTry English song names for better results."

# ==================== FORCE SUBSCRIBE ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Subscribe check error: {e}")
        return False

# ==================== COMMANDS ====================
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    welcome = f"""
🎵 **NAMASTE {first_name}!** 🙏

🎤 **KARAOKE BOT - UNLIMITED EDITION** 🚀

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
`/song shape of you`
`/song dilbar`
`/song satranga`
`/song heeriye`
"""
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, welcome + "\n👑 **ADMIN MODE**")
        return
    
    if not is_subscribed(user_id):
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK)
        )
        bot.send_message(message.chat.id, 
            "🚫 **JOIN CHANNEL FIRST!**\n\n"
            f"📢 [JOIN HERE]({CHANNEL_LINK})\n\n"
            "Bot use karne ke liye channel join karein!",
            reply_markup=markup, parse_mode='Markdown', disable_web_page_preview=True)
        return
    
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown')

@bot.message_handler(commands=['song'])
def song_handler(message):
    user_id = message.from_user.id
    
    # Check subscription
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Join channel first!**\n\nUse: `/song [song name]`")
        return
    
    query = message.text[6:].strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/song tum hi ho`\n\nTry: `/song kesariya`")
        return
    
    # Send searching message
    search_msg = bot.reply_to(message, f"🔍 **Searching:** `{query}`\n\n⏳ Please wait...")
    
    # Try async search first
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        music = loop.run_until_complete(search_song_async(query))
    except Exception as e:
        logger.error(f"Async error: {e}")
        music = None
    finally:
        loop.close()
    
    # Fallback to sync if async fails
    if not music or not music.get('url'):
        logger.info("🔄 Trying fallback search...")
        music = search_song_sync(query)
    
    if music and music.get('url'):
        try:
            # Create caption
            caption = (
                f"🎵 **{music['title']}**\n"
                f"👤 **{music['artist']}**\n"
                f"✨ **320kbps HD** ✅\n\n"
                f"🔗 Requested by: @{message.from_user.username or 'User'}"
            )
            
            # Try to send audio
            try:
                # Method 1: Direct URL (faster)
                bot.send_audio(
                    message.chat.id, 
                    music['url'],
                    caption=caption,
                    title=music['title'],
                    performer=music['artist']
                )
                logger.info(f"✅ Sent: {music['title']}")
                
            except Exception as e:
                logger.error(f"Direct send failed: {e}")
                
                # Method 2: Download and send
                try:
                    resp = requests.get(music['url'], timeout=20)
                    if resp.status_code == 200:
                        audio_file = io.BytesIO(resp.content)
                        bot.send_audio(
                            message.chat.id,
                            audio_file,
                            caption=caption,
                            title=music['title'],
                            performer=music['artist']
                        )
                        logger.info(f"✅ Sent (downloaded): {music['title']}")
                    else:
                        raise Exception("Download failed")
                except Exception as download_error:
                    logger.error(f"Download error: {download_error}")
                    bot.edit_message_text(
                        f"❌ **Song found but cannot send!**\n\n"
                        f"🎵 **{music['title']}**\n"
                        f"👤 **{music['artist']}**\n\n"
                        f"Try another song or use `/songLY`",
                        message.chat.id, search_msg.message_id
                    )
                    return
            
            # Delete search message
            bot.delete_message(message.chat.id, search_msg.message_id)
            
            # Success message
            success_msg = bot.reply_to(message, f"✅ **{music['title']}** sent! 🎶")
            
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
            logger.error(f"Send error: {e}")
            bot.edit_message_text(
                f"❌ **Error sending song!**\n\n"
                f"🔍 Searched: `{query}`\n\n"
                f"**Try:** `/song tum hi ho`",
                message.chat.id, search_msg.message_id,
                parse_mode='Markdown'
            )
    else:
        bot.edit_message_text(
            f"❌ **Song not found!** 😔\n\n"
            f"🔍 Searched: `{query}`\n\n"
            f"**💡 Tips:**\n"
            f"• Use exact song name\n"
            f"• Try: `/song tum hi ho`\n"
            f"• Try: `/song kesariya`\n"
            f"• Try: `/song dilbar`",
            message.chat.id, search_msg.message_id,
            parse_mode='Markdown'
        )

@bot.message_handler(commands=['songLY'])
def songlyrics_handler(message):
    """Song + Lyrics together"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Join channel first!**")
        return
    
    query = message.text[7:].strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/songLY tum hi ho`")
        return
    
    # Send processing message
    process_msg = bot.reply_to(message, f"🎨 **Processing:** `{query}`\n\n⏳ Song + Lyrics coming...")
    
    # Get song
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        music = loop.run_until_complete(search_song_async(query))
    except:
        music = search_song_sync(query)
    finally:
        loop.close()
    
    # Send song if found
    if music and music.get('url'):
        try:
            caption = f"🎵 **{music['title']}** - Lyrics below! 👇"
            bot.send_audio(message.chat.id, music['url'], caption=caption)
        except:
            pass
    
    # Get and send lyrics
    lyrics = get_lyrics(query)
    bot.send_message(message.chat.id, lyrics, parse_mode='Markdown')
    
    # Clean up
    bot.delete_message(message.chat.id, process_msg.message_id)

@bot.message_handler(commands=['lyrics'])
def lyrics_handler(message):
    """Only lyrics"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is
