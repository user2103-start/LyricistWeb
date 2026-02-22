import telebot
import requests
import time
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import lyricsgenius
from urllib.parse import quote
from flask import Flask, request
import jiosaavn  # JioSaavn API!

# ==================== CONFIG ====================
BOT_TOKEN = "8454384380:AAH1XIgIJ4qnzvJasPCNgpU7rSlPbiflbRY"
CHANNEL_ID = "-1003751644036"
CHANNEL_LINK = "https://t.me/+JPgViOHx7bdlMDZl"
ADMIN_ID = 6593129349
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)
genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False)

print("🎵 JIO SAAVN BOT LIVE!")

# ==================== FORCE SUBSCRIBE ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ==================== JIO SAAVN MAGIC! ====================
def get_saavn_song(query):
    try:
        # Search JioSaavn
        results = jiosaavn.search(query)
        if results and len(results) > 0:
            song = results[0]  # Best match
            download_url = jiosaavn.download_song(song['id'], quality='320')
            
            return {
                'url': download_url,
                'title': song.get('song', query),
                'artist': song.get('primary_artists', 'Artist'),
                'success': True
            }
    except Exception as e:
        print(f"Saavn error: {e}")
        pass
    
    return None

# Fallback APIs
def get_fallback_song(query):
    apis = [
        "https://free-music-api2.vercel.app/getSongs",
        "https://music-api-tau.vercel.app/getSongs"
    ]
    
    for api in apis:
        try:
            resp = requests.get(f"{api}?q={quote(query)}", timeout=8).json()
            if isinstance(resp, list) and len(resp) > 0:
                song = resp[0]
                url = song.get('download_url') or song.get('url')
                if url:
                    return {
                        'url': url,
                        'title': song.get('title', query),
                        'artist': song.get('artist', 'Music'),
                        'success': True
                    }
        except:
            continue
    return None

# ==================== MAIN SONG FUNCTION ====================
def get_song(query):
    # Priority 1: JioSaavn (Hindi songs king!)
    song = get_saavn_song(query)
    if song:
        return song
    
    # Priority 2: Fallback
    song = get_fallback_song(query)
    if song:
        return song
    
    return None

# ==================== VISUAL LYRICS ====================
def get_visual_lyrics(query):
    try:
        songs = genius.search(query)
        if songs:
            song = songs[0]
            lyrics = genius.lyrics(song.id)
            lines = [l.strip() for l in lyrics.split('\n') if l.strip()][:20]
            
            visual = "🎤 **VISUAL LYRICS** 🎵\n\n"
            for i, line in enumerate(lines, 1):
                emoji = "✨" if i % 2 else "🎶"
                visual += f"`{line}` {emoji}\n"
            
            visual += f"\n👤 **{song.artist}**\n🎵 **{song.title}**"
            return visual
    except:
        pass
    return None

# ==================== COMMANDS ====================

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    
    welcome = (
        "🎨 **Welcome to VISUAL LYRICS!** 🚀\n\n"
        "🌟 **JioSaavn + Premium Music**\n\n"
        "**Try:**\n"
        "`/song gehra hua`\n"
        "`/song tum hi ho`\n"
        "`/songLY dilbar`"
    )
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, welcome + "\n\n👑 **ADMIN**")
        return
    
    if not is_subscribed(user_id):
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK)
        )
        bot.send_message(message.chat.id, 
            "🚫 **JOIN FIRST!**\n\n"
            f"[📢 Channel]({CHANNEL_LINK})", 
            reply_markup=markup, disable_web_page_preview=True)
        return
    
    bot.send_message(message.chat.id, welcome)

@bot.message_handler(commands=['song'])
def song_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Join channel!**")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ **`/song gehra hua`**")
        return
    
    bot.reply_to(message, f"🎵 **{query}** loading...")
    
    music = get_song(query)
    if music and music.get('url'):
        try:
            caption = f"🎵 **{music['title']}**\n👤 **{music['artist']}**\n✨ **320kbps**"
            bot.send_audio(message.chat.id, music['url'], 
                          caption=caption,
                          title=music['title'],
                          performer=music['artist'])
            bot.reply_to(message, f"✅ **{music['title']}** 🎶")
        except:
            bot.reply_to(message, "❌ **Download error!**")
    else:
        bot.reply_to(message, f"❌ **{query}** not found!\nTry `tum hi ho`, `dilbar`")

@bot.message_handler(commands=['songLY'])
def songlyrics_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Join channel!**")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ **`/songLY kal ho naa ho`**")
        return
    
    bot.reply_to(message, f"🎨 **{query}** Visual Lyrics...")
    
    # Song + Lyrics
    music = get_song(query)
    if music and music.get('url'):
        try:
            bot.send_audio(message.chat.id, music['url'], 
                          caption=f"🎵 **{music['title']}** 🎤 Lyrics below!")
        except:
            pass
    
    lyrics = get_visual_lyrics(query)
    if lyrics:
        bot.send_message(message.chat.id, lyrics)
    else:
        bot.send_message(message.chat.id, f"❌ **Lyrics** not found!")

@bot.message_handler(commands=['admin'])
def admin_handler(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Broadcast", callback_data="bc"))
    markup.row(InlineKeyboardButton("✅ Status", callback_data="status"))
    
    bot.send_message(message.chat.id, "🔥 **ADMIN PANEL**\n✅ JioSaavn Active!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    if call.data == "bc":
        bot.send_message(call.message.chat.id, "📢 **Broadcast:**")
        bot.register_next_step_handler(call.message, lambda m: broadcast(m))
    elif call.data == "status":
        bot.edit_message_text("✅ **LIVE!**\n🎵 JioSaavn 320kbps\n🔗 4 APIs Backup", 
                            call.message.chat.id, call.message.id)

def broadcast(message):
    try:
        bot.send_message(CHANNEL_ID, message.text)
        bot.reply_to(message, "✅ **Sent!** 📢")
    except:
        bot.reply_to(message, "❌ **Failed!**")

# ==================== WEBHOOK (No 409!) ====================
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK"

@app.route('/')
def index():
    return "🎵 VISUAL LYRICS LIVE!"

if __name__ == '__main__':
    bot.delete_webhook()
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook: {webhook_url}")
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
