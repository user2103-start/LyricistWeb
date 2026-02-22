import telebot
import requests
import time
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import lyricsgenius
from urllib.parse import quote
from flask import Flask, request
from jiosaavn import JioSaavn  # ✅ CORRECT IMPORT!

# ==================== CONFIG ====================
BOT_TOKEN = "8454384380:AAH1XIgIJ4qnzvJasPCNgpU7rSlPbiflbRY"
CHANNEL_ID = "-1003751644036"
CHANNEL_LINK = "https://t.me/+JPgViOHx7bdlMDZl"
ADMIN_ID = 6593129349
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)
genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False)
saavn = JioSaavn()  # JioSaavn Instance

print("🎵 JIO SAAVN BOT LIVE!")

# ==================== FORCE SUBSCRIBE ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ==================== JIO SAAVN 320KBPS! ====================
def get_saavn_song(query):
    try:
        # Search songs
        results = saavn.search(query)
        if results and len(results['songs']) > 0:
            song_info = results['songs'][0]
            song_id = song_info['id']
            
            # Get direct 320kbps download
            download_info = saavn.get_song_direct_link(song_id)
            if download_info and '320' in download_info:
                return {
                    'url': download_info['320'],
                    'title': song_info.get('song', query),
                    'artist': song_info.get('primary_artists', 'Artist'),
                    'success': True
                }
    except Exception as e:
        print(f"Saavn error: {e}")
    
    return None

# Fallback APIs (Backup)
def get_fallback_song(query):
    apis = [
        "https://free-music-api2.vercel.app/getSongs?q=",
        "https://music-api-tau.vercel.app/getSongs?q=",
        "https://music-api-nine.vercel.app/getSongs?q=",
        "https://aurora-music-api.vercel.app/getSongs?q="
    ]
    
    for api_url in apis:
        try:
            resp = requests.get(api_url + quote(query), timeout=10).json()
            if isinstance(resp, list) and len(resp) > 0:
                song = resp[0]
                url = song.get('download_url') or song.get('url') or song.get('320')
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

# ==================== MAIN SONG ENGINE ====================
def get_song(query):
    song = get_saavn_song(query)
    if song:
        return song
    
    song = get_fallback_song(query)
    if song:
        return song
    
    return None

# ==================== GENIUS LYRICS ====================
def get_visual_lyrics(query):
    try:
        songs = genius.search(query)
        if songs and len(songs) > 0:
            song = songs[0]
            lyrics = genius.lyrics(song.id)
            lines = [l.strip() for l in lyrics.split('\n') if l.strip()][:15]
            
            visual = "🎤 **VISUAL LYRICS** 🎵\n\n"
            for i, line in enumerate(lines, 1):
                emoji = "✨" if i % 2 else "🎶"
                visual += f"{emoji} `{line}`\n"
            
            visual += f"\n👤 **{song.artist}** | 🎵 **{song.title}**"
            return visual
    except:
        pass
    return "❌ **Lyrics not found!**"

# ==================== COMMANDS ====================
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    
    welcome = (
        "🎨 **KARAOKE BOT LIVE!** 🚀\n\n"
        "🎵 **JioSaavn 320kbps**\n"
        "✨ **Visual Lyrics**\n\n"
        "**Commands:**\n"
        "`/song gehra hua`\n"
        "`/songLY tum hi ho`\n"
        "`/song dilbar`"
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
        bot.reply_to(message, "❌ **Use:** `/song gehra hua`")
        return
    
    msg = bot.reply_to(message, f"🔍 **Searching {query}**...")
    
    music = get_song(query)
    if music and music.get('url'):
        try:
            caption = f"🎵 **{music['title']}**\n👤 **{music['artist']}**\n✨ **320kbps**"
            bot.send_audio(message.chat.id, music['url'], 
                          caption=caption,
                          title=music['title'],
                          performer=music['artist'])
            bot.delete_message(message.chat.id, msg.message_id)
            bot.reply_to(message, f"✅ **{music['title']}** 🎶")
        except Exception as e:
            bot.edit_message_text("❌ **Download failed!** Try another song.", 
                                message.chat.id, msg.message_id)
    else:
        bot.edit_message_text(f"❌ **'{query}'** not found!\n\n"
                            "✅ **Try:** `tum hi ho`, `dilbar`, `kal ho naa ho`", 
                            message.chat.id, msg.message_id)

@bot.message_handler(commands=['songLY'])
def songlyrics_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Join channel!**")
        return
    
    query = message.text[7:].strip()
    if not query:
        bot.reply_to(message, "❌ **Use:** `/songLY kal ho naa ho`")
        return
    
    msg = bot.reply_to(message, f"🎨 **{query}** Visual Lyrics...")
    
    # Send song first
    music = get_song(query)
    if music and music.get('url'):
        try:
            bot.send_audio(message.chat.id, music['url'], 
                          caption=f"🎵 **{music['title']}** 🎤 Lyrics below!")
        except:
            pass
    
    # Send lyrics
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
    markup.row(InlineKeyboardButton("🔄 Restart", callback_data="restart"))
    
    bot.send_message(message.chat.id, 
        "🔥 **ADMIN PANEL**\n"
        "✅ JioSaavn Active\n"
        "✅ Genius Lyrics\n"
        "✅ 4 Fallback APIs", 
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    bot.answer_callback_query(call.id)
    
    if call.data == "bc":
        bot.send_message(call.message.chat.id, "📢 **Broadcast to channel:**")
        bot.register_next_step_handler(call.message, lambda m: broadcast(m))
    elif call.data == "status":
        bot.edit_message_text("✅ **BOT LIVE!**\n🎵 JioSaavn 320kbps\n🔗 Webhook Active", 
                            call.message.chat.id, call.message.id)
    elif call.data == "restart":
        bot.edit_message_text("🔄 **Restarting...**", call.message.chat.id, call.message.id)

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
    return "OK"

@app.route('/')
def index():
    return "🎵 **KARAOKE BOT LIVE!** JioSaavn 320kbps"

if __name__ == '__main__':
    bot.remove_webhook()
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost:5000')}/{BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook set: {webhook_url}")
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
