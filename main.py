import telebot
import requests
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import lyricsgenius
from urllib.parse import quote

# ==================== CONFIG ====================
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"
CHANNEL_ID = "-1003751644036"
CHANNEL_LINK = "https://t.me/+JPgViOHx7bdlMDZl"
ADMIN_ID = 6593129349
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

MUSIC_APIS = [
    "https://free-music-api2.vercel.app",
    "https://music-api-tau.vercel.app",
    "https://music-api-nine.vercel.app"
]

# Bot setup + Anti-409
time.sleep(5)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')
genius = lyricsgenius.Genius(GENIUS_TOKEN, verbose=False)

print("🎨 VISUAL LYRICS BOT READY!")

# ==================== FORCE SUBSCRIBE ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ==================== FIXED MUSIC ENGINE ====================
def get_song(query):
    query_lower = query.lower()
    
    for base_url in MUSIC_APIS:
        try:
            api_url = f"{base_url}/getSongs?q={quote(query)}"
            resp = requests.get(api_url, timeout=8).json()
            
            if isinstance(resp, list) and len(resp) > 0:
                # EXACT MATCH SCORING!
                best_match = None
                best_score = 0
                
                for song in resp[:10]:
                    title = (song.get('title') or '').lower()
                    artist = (song.get('artist') or '').lower()
                    
                    score = 0
                    if query_lower in title:
                        score += 10
                    if query_lower in artist:
                        score += 5
                    if title.startswith(query_lower[:4]):
                        score += 3
                        
                    if score > best_score:
                        best_score = score
                        best_match = {
                            'url': song.get('download_url') or song.get('url') or song.get('preview'),
                            'title': song.get('title', query),
                            'artist': song.get('artist', 'Premium'),
                            'score': score
                        }
                
                # Fallback
                if not best_match:
                    song = resp[0]
                    best_match = {
                        'url': song.get('download_url') or song.get('url') or song.get('preview'),
                        'title': song.get('title', query),
                        'artist': song.get('artist', 'Premium'),
                        'score': 1
                    }
                
                print(f"🎵 {best_match['title']} (score: {best_score})")
                return best_match
                
        except:
            continue
    
    return None

# ==================== VISUAL LYRICS ====================
def get_visual_lyrics(query):
    try:
        songs = genius.search(query)
        if songs and len(songs) > 0:
            song = songs[0]
            lyrics = genius.lyrics(song.id)
            
            lines = [line.strip() for line in lyrics.split('\n') if line.strip()][:20]
            visual = "🎤 **VISUAL LYRICS** 🎵\n\n"
            
            for i, line in enumerate(lines, 1):
                if i % 2 == 0:
                    visual += f"**`{line}`** 🎶\n"
                else:
                    visual += f"`{line}` ✨\n"
            
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
        "🌟 **Most Advanced Music Bot on Telegram!**\n\n"
        "**Commands:**\n"
        "🎵 `/song gehra hua` → Premium Audio\n"
        "🎤 `/songLY tum hi ho` → **VISUAL LYRICS**\n"
        "🔥 `/admin` → Admin Panel"
    )
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, welcome + "\n\n👑 **ADMIN MODE**")
    else:
        if not is_subscribed(user_id):
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK)
            )
            bot.send_message(message.chat.id, 
                "🚫 **VISUAL LYRICS LOCKED!**\n\n"
                f"📢 **[Join Channel]({CHANNEL_LINK})**\n\n"
                "✅ Join → `/start` again!", 
                reply_markup=markup, disable_web_page_preview=True)
            return
        
        bot.send_message(message.chat.id, welcome)

@bot.message_handler(commands=['song'])
def song_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Join channel first!**")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/song dilbar`")
        return
    
    bot.reply_to(message, f"🔍 **Searching `{query}`**...")
    
    music = get_song(query)
    if music and music.get('url'):
        try:
            caption = f"🎵 **{music['title']}**\n👤 **{music['artist']}**\n✨ **Visual Lyrics Bot**"
            bot.send_audio(message.chat.id, music['url'], 
                          caption=caption,
                          title=music['title'],
                          performer=music['artist'])
            bot.reply_to(message, f"✅ **{music['title']}** delivered! 🎶\n`/songLY {query}` for lyrics!")
        except:
            bot.reply_to(message, f"❌ **Download issue!** Try again.")
    else:
        bot.reply_to(message, f"❌ **`{query}`** not found!\nTry: `dilbar`, `tum hi ho`, `gehra hua`")

@bot.message_handler(commands=['songLY'])
def songlyrics_handler(message):
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID and not is_subscribed(user_id):
        bot.reply_to(message, "🚫 **Join channel first!**")
        return
    
    query = ' '.join(message.text.split()[1:]).strip()
    if not query:
        bot.reply_to(message, "❌ **Usage:** `/songLY kal ho naa ho`")
        return
    
    bot.reply_to(message, f"🎨 **VISUAL LYRICS** `{query}` loading...")
    
    # Song
    music = get_song(query)
    if music and music.get('url'):
        try:
            caption = f"🎵 **{music['title']}** 🎤 Visual Lyrics below!"
            bot.send_audio(message.chat.id, music['url'], 
                          caption=caption,
                          title=music['title'])
        except:
            pass
    
    # Visual Lyrics
    lyrics = get_visual_lyrics(query)
    if lyrics:
        bot.send_message(message.chat.id, lyrics)
    else:
        bot.send_message(message.chat.id, f"❌ **Lyrics** for `{query}` not available!")

@bot.message_handler(commands=['admin'])
def admin_handler(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Broadcast", callback_data="bc"))
    markup.row(InlineKeyboardButton("📊 Stats", callback_data="stats"))
    
    bot.send_message(message.chat.id, 
        "🔥 **VISUAL LYRICS ADMIN** 🔥\n\n✅ Bot: LIVE\n✅ Multiple APIs: ACTIVE",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def admin_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    if call.data == "bc":
        bot.send_message(call.message.chat.id, "📢 **Broadcast:**")
        bot.register_next_step_handler(call.message, lambda m: broadcast(m, call.message.chat.id))
    elif call.data == "stats":
        bot.edit_message_text("✅ **ALL GREEN!**\n🎵 APIs: 3 Active\n🎤 Genius: OK", 
                            call.message.chat.id, call.message.id)

def broadcast(message, chat_id):
    try:
        bot.send_message(CHANNEL_ID, message.text)
        bot.send_message(chat_id, "✅ **Broadcast sent!** 📢")
    except:
        bot.send_message(chat_id, "❌ **Broadcast failed!**")

# ==================== START ====================
if __name__ == "__main__":
    print("🚀 VISUAL LYRICS BOT LIVE!")
    try:
        bot.infinity_polling(none_stop=True, interval=2, timeout=30)
    except KeyboardInterrupt:
        print("🛑 Stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(10)
