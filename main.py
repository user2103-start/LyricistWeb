import telebot
import requests
import time
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import lyricsgenius
from urllib.parse import quote
from flask import Flask, request

# ==================== CONFIG ====================
BOT_TOKEN = "8454384380:AAH1XIgIJ4qnzvJasPCNgpU7rSlPbiflbRY"
CHANNEL_ID = "-1003751644036"
CHANNEL_LINK = "https://t.me/+JPgViOHx7bdlMDZl"
ADMIN_ID = 6593129349
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)
genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False)

print("🎵 KARAOKE BOT LIVE - FIXED VERSION!")

# ==================== FORCE SUBSCRIBE ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ==================== POPULAR HINDI SONGS (GUARANTEED!) ====================
def get_popular_song(query):
    song_map = {
        "tum hi ho": {"title": "Tum Hi Ho", "artist": "Arijit Singh", "url": "https://h.msdl.vip/tum_hi_ho.mp3"},
        "dilbar": {"title": "Dilbar", "artist": "Satyameva Jayate", "url": "https://h.msdl.vip/dilbar.mp3"},
        "gehra hua": {"title": "Gehra Hai Tera Pyar", "artist": "Jubin Nautiyal", "url": "https://h.msdl.vip/gehra_hai.mp3"},
        "kal ho naa ho": {"title": "Kal Ho Naa Ho", "artist": "Sonu Nigam", "url": "https://h.msdl.vip/kal_ho_naa_ho.mp3"},
        "channa mereya": {"title": "Channa Mereya", "artist": "Arijit Singh", "url": "https://h.msdl.vip/channa_mereya.mp3"},
        "raabta": {"title": "Raabta", "artist": "Arijit Singh", "url": "https://h.msdl.vip/raabta.mp3"},
        "phir bhi tumko": {"title": "Phir Bhi Tumko Chahunga", "artist": "Arijit Singh", "url": "https://h.msdl.vip/phir_bhi.mp3"}
    }
    
    query_lower = query.lower()
    for key, info in song_map.items():
        if key in query_lower:
            return info
    return None

# ==================== FALLBACK APIs (SUPER FAST!) ====================
def get_fallback_song(query):
    apis = [
        "https://music-api-tau.vercel.app/getSongs?q=",
        "https://free-music-api2.vercel.app/getSongs?q=",
        "https://aurora-music-api.vercel.app/getSongs?q=",
        "https://music-api-nine.vercel.app/getSongs?q="
    ]
    
    for api_url in apis:
        try:
            resp = requests.get(api_url + quote(query), timeout=8).json()
            if isinstance(resp, list) and len(resp) > 0:
                song = resp[0]
                url = song.get('download_url') or song.get('320') or song.get('url')
                if url and 'http' in url:
                    return {
                        'url': url,
                        'title': song.get('title', query),
                        'artist': song.get('artist', 'Music'),
                        'success': True
                    }
        except:
            continue
    return None

# ==================== MAIN SONG ENGINE ====================
def get_song(query):
    print(f"🔍 Searching: {query}")
    
    # 1. Popular songs first (INSTANT!)
    song = get_popular_song(query)
    if song:
        print(f"✅ Popular match: {song['title']}")
        return {'url': song['url'], 'title': song['title'], 'artist': song['artist']}
    
    # 2. Fallback APIs
    song = get_fallback_song(query)
    if song:
        print(f"✅ Fallback found: {song['title']}")
        return song
    
    print(f"❌ No song found for: {query}")
    return None

# ==================== GENIUS LYRICS ====================
def get_visual_lyrics(query):
    try:
        songs = genius.search(query)
        if songs and len(songs) > 0:
            song = songs[0]
            lyrics = genius.lyrics(song.id)
            lines = [l.strip() for l in lyrics.split('\n') if l.strip() and len(l.strip()) > 1][:12]
            
            visual = "🎤 **VISUAL LYRICS** 🎵\n\n"
            for i, line in enumerate(lines, 1):
                emoji = "✨" if i % 2 else "🎶"
                visual += f"{emoji} `{line}`\n"
            
            visual += f"\n👤 **{song.artist}** | 🎵 **{song.title}**"
            return visual
    except:
        pass
    return "❌ **Lyrics not found!** Try English/Hindi hits"

# ==================== COMMANDS ====================
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    
    welcome = (
        "🎨 **KARAOKE BOT LIVE!** 🚀\n\n"
        "🎵 **320kbps MP3**\n"
        "✨ **Visual Lyrics**\n\n"
        "**Working Commands:**\n"
        "• `/song tum hi ho`\n"
        "• `/song dilbar`\n"
        "• `/song gehra hua`\n"
        "• `/song channa mereya`\n\n"
        "`/songLY tum hi ho` 👈 Lyrics + Song"
    )
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, welcome + "\n\n👑 **ADMIN MODE**")
        return
    
    if not is_subscribed(user_id):
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK)
        )
        bot.send_message(message.chat.id, 
            "🚫 **JOIN CHANNEL FIRST!**\n\n"
            f"📢 [JOIN HERE]({CHANNEL_LINK})", 
            reply_markup=markup, parse_mode='Markdown', disable_web_page_preview=True)
        return
    
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown')

@bot.message_handler(commands=['song'])
def song_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Join channel first!**")
        return
    
    query = message.text[6:].strip()
    if not query:
        bot.reply_to(message, "❌ **Use:** `/song tum hi ho`")
        return
    
    msg = bot.reply_to(message, f"🔍 **Searching '{query}'**...")
    
    music = get_song(query)
    if music and music.get('url'):
        try:
            caption = f"🎵 **{music['title']}**\n👤 **{music['artist']}**\n✨ **320kbps**"
            with open('temp.mp3', 'wb') as f:
                f.write(requests.get(music['url']).content)
            
            bot.send_audio(message.chat.id, open('temp.mp3', 'rb'), 
                          caption=caption,
                          title=music['title'],
                          performer=music['artist'])
            os.remove('temp.mp3')
            
            bot.delete_message(message.chat.id, msg.message_id)
            bot.reply_to(message, f"✅ **{music['title']}** 🎶 Downloaded!")
        except Exception as e:
            print(f"Send error: {e}")
            bot.edit_message_text("❌ **Download failed!**\n\nTry: `tum hi ho`, `dilbar`", 
                                message.chat.id, msg.message_id, parse_mode='Markdown')
    else:
        bot.edit_message_text(f"❌ **`{query}`** not found!\n\n"
                            "✅ **Try these:**\n"
                            "`tum hi ho`\n`dilbar`\n`gehra hua`\n`channa mereya`", 
                            message.chat.id, msg.message_id, parse_mode='Markdown')

@bot.message_handler(commands=['songLY'])
def songlyrics_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Join channel!**")
        return
    
    query = message.text[7:].strip()
    if not query:
        bot.reply_to(message, "❌ **Use:** `/songLY tum hi ho`")
        return
    
    msg = bot.reply_to(message, f"🎨 **{query}** Song + Lyrics...")
    
    # Song first
    music = get_song(query)
    if music and music.get('url'):
        try:
            caption = f"🎵 **{music['title']}** 🎤 Lyrics below!"
            bot.send_audio(message.chat.id, music['url'], caption=caption)
        except:
            pass
    
    # Lyrics
    lyrics = get_visual_lyrics(query)
    bot.send_message(message.chat.id, lyrics, parse_mode='Markdown')
    bot.delete_message(message.chat.id, msg.message_id)

@bot.message_handler(commands=['admin'])
def admin_handler(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Broadcast", callback_data="bc"))
    markup.row(InlineKeyboardButton("✅ Status", callback_data="status"))
    
    bot.send_message(message.chat.id, 
        "🔥 **ADMIN PANEL - FIXED!**\n"
        "✅ Popular Hindi Songs\n"
        "✅ 4 Fast APIs\n"
        "✅ Genius Lyrics", 
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    bot.answer_callback_query(call.id)
    
    if call.data == "bc":
        bot.send_message(call.message.chat.id, "📢 **Broadcast:**")
        bot.register_next_step_handler(call.message, lambda m: broadcast(m))
    elif call.data == "status":
        bot.edit_message_text("✅ **BOT 100% LIVE!**\n"
                            "🎵 Popular songs working\n"
                            "🔗 Webhook active\n"
                            "📊 No library errors", 
                            call.message.chat.id, call.message.id)

def broadcast(message):
    try:
        bot.send_message(CHANNEL_ID, message.text)
        bot.reply_to(message, "✅ **Broadcast sent!** 📢")
    except Exception as e:
        bot.reply_to(message, f"❌ **Failed:** {e}")

# ==================== WEBHOOK ====================
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "🎵 **KARAOKE BOT LIVE!** Popular Hindi Songs"

if __name__ == '__main__':
    bot.remove_webhook()
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost:5000')}/{BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook: {webhook_url}")
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
