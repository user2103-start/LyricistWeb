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

MUSIC_APIS = [
    "https://free-music-api2.vercel.app",
    "https://music-api-tau.vercel.app",
    "https://music-api-nine.vercel.app",
    "https://aurora-music-api.vercel.app"
]

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)
genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False)

print("🎨 VISUAL LYRICS WEBHOOK READY!")

# ==================== FORCE SUBSCRIBE ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ==================== MUSIC ENGINE ====================
def get_song(query):
    query_lower = query.lower()
    
    for base_url in MUSIC_APIS:
        try:
            api_url = f"{base_url}/getSongs?q={quote(query)}"
            resp = requests.get(api_url, timeout=8).json()
            
            if isinstance(resp, list) and len(resp) > 0:
                best_match = None
                best_score = 0
                
                for song in resp[:15]:
                    title = (song.get('title') or '').lower()
                    artist = (song.get('artist') or '').lower()
                    
                    score = 0
                    if query_lower in title:
                        score += 15
                    if query_lower in artist:
                        score += 10
                    if len(query_lower.split()) == 1 and query_lower in title:
                        score += 20
                        
                    if score > best_score:
                        best_score = score
                        best_match = {
                            'url': next((song.get(x) for x in ['download_url', 'url', 'preview'] if song.get(x)), None),
                            'title': song.get('title', query),
                            'artist': song.get('artist', 'Music'),
                            'score': score
                        }
                
                if best_match and best_match['url']:
                    return best_match
                        
        except:
            continue
    
    return None

# ==================== VISUAL LYRICS ====================
def get_visual_lyrics(query):
    try:
        songs = genius.search(query)
        if songs:
            song = songs[0]
            lyrics = genius.lyrics(song.id)
            lines = [l.strip() for l in lyrics.split('\n') if l.strip()][:25]
            
            visual = "🎤 *VISUAL LYRICS* 🎵\n\n"
            for i, line in enumerate(lines, 1):
                emoji = "✨" if i % 2 else "🎶"
                visual += f"`{line}` {emoji}\n"
            
            visual += f"\n👤 *{song.artist}*\n🎵 *{song.title}*"
            return visual
    except:
        pass
    return None

# ==================== COMMANDS ====================

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    
    welcome = (
        "🎨 *Welcome to VISUAL LYRICS!* 🚀\n\n"
        "🌟 *Most Advanced Music Bot*\n\n"
        "*Commands:*\n"
        "🎵 `/song gehra hua`\n"
        "🎤 `/songLY tum hi ho`\n"
        "🔥 `/admin`"
    )
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, welcome + "\n\n👑 *ADMIN ACTIVE*")
    else:
        if not is_subscribed(user_id):
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK)
            )
            bot.send_message(message.chat.id, 
                "🚫 *LOCKED!*\n\n"
                f"📢 [Join Channel]({CHANNEL_LINK})\n\n"
                "✅ Join → `/start`", 
                reply_markup=markup, disable_web_page_preview=True)
            return
        
        bot.send_message(message.chat.id, welcome)

@bot.message_handler(commands=['song'])
def song_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 *Join channel!*")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ */song dilbar*")
        return
    
    bot.reply_to(message, f"🔍 *`{query}`* searching...")
    
    music = get_song(query)
    if music and music.get('url'):
        try:
            caption = f"🎵 *{music['title']}*\n👤 *{music['artist']}*\n✨ *Visual Lyrics*"
            bot.send_audio(message.chat.id, music['url'], 
                          caption=caption,
                          title=music['title'],
                          performer=music['artist'])
            bot.reply_to(message, f"✅ *{music['title']}* 🎶\n`/songLY {query}`")
        except:
            bot.reply_to(message, "❌ *Download failed!*")
    else:
        bot.reply_to(message, f"❌ *`{query}`* not found!\nTry `dilbar`, `tum hi ho`")

@bot.message_handler(commands=['songLY'])
def songlyrics_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 *Join channel!*")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ */songLY kal ho naa ho*")
        return
    
    bot.reply_to(message, f"🎨 *VISUAL LYRICS* `{query}`...")
    
    music = get_song(query)
    if music and music.get('url'):
        try:
            bot.send_audio(message.chat.id, music['url'], 
                          caption=f"🎵 *{music['title']}* 🎤 Lyrics below!",
                          title=music['title'])
        except:
            pass
    
    lyrics = get_visual_lyrics(query)
    if lyrics:
        bot.send_message(message.chat.id, lyrics)
    else:
        bot.send_message(message.chat.id, f"❌ *Lyrics* `{query}` not available!")

@bot.message_handler(commands=['admin'])
def admin_handler(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Broadcast", callback_data="bc"))
    markup.row(InlineKeyboardButton("📊 Status", callback_data="status"))
    
    bot.send_message(message.chat.id, "🔥 *ADMIN PANEL* 🔥", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    if call.data == "bc":
        bot.send_message(call.message.chat.id, "📢 *Broadcast message:*")
        bot.register_next_step_handler(call.message, lambda m: send_broadcast(m))
    elif call.data == "status":
        bot.edit_message_text("✅ *WEBHOOK LIVE!*\n🎵 4 APIs Active\n🎤 Genius OK", 
                            call.message.chat.id, call.message.id)

def send_broadcast(message):
    try:
        bot.send_message(CHANNEL_ID, message.text)
        bot.reply_to(message, "✅ *Broadcast sent!* 📢")
    except:
        bot.reply_to(message, "❌ *Failed!*")

# ==================== WEBHOOK ====================
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'ok'

@app.route('/')
def index():
    return "🎨 VISUAL LYRICS BOT LIVE! 🚀"

if __name__ == '__main__':
    # Delete webhook + Set new
    try:
        bot.delete_webhook()
        bot.set_webhook(url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}")
        print("✅ WEBHOOK SET!")
    except:
        pass
    
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 8443)))
