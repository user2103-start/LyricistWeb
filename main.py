import telebot
import requests
import os
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv('BOT_TOKEN')  # @BotFather se
CHANNEL_ID = os.getenv('CHANNEL_ID')  # "-100xxxxxxxxxx" format
ADMIN_ID = int(os.getenv('ADMIN_ID'))  # Tera Telegram ID

MUSIC_API = "https://free-music-api2.vercel.app"
FALLBACK_API = "https://bhindi1.ddns.net/music/api/prepare/"

bot = telebot.TeleBot(BOT_TOKEN)

# ==================== FORCE SUBSCRIBE CHECK ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def get_subscribe_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("📢 Channel Join Karo", url=f"https://t.me/{CHANNEL_ID[4:]}"),
        InlineKeyboardButton("✅ Check Subscription", callback_data="check_sub")
    )
    return markup

# ==================== MAIN MUSIC SEARCH ====================
def search_music(query):
    """Multiple APIs try karega"""
    
    # API 1: Free Music API
    try:
        if 'arijit' in query.lower():
            url = f"{MUSIC_API}/album/arijitsingh"
        else:
            url = f"{MUSIC_API}/getSongs"
        
        resp = requests.get(url, timeout=15).json()
        songs = resp if isinstance(resp, list) else resp.get('songs', [])
        
        if songs:
            song = songs[0] if isinstance(songs[0], dict) else songs[0]
            dl_url = song.get('download_url') or song.get('audio_url') or song.get('url')
            title = song.get('title', 'Premium Song')
            artist = song.get('artist', 'Artist')
            
            if dl_url:
                return {
                    'url': dl_url,
                    'title': title,
                    'artist': artist,
                    'success': True
                }
    except:
        pass
    
    # Fallback: YouTube Music
    try:
        yt_url = f"https://ytapi-cloud.onrender.com/download?query={quote(query + ' official audio')}"
        resp = requests.get(yt_url, timeout=15).json()
        if resp.get('success'):
            return {
                'url': resp['url'],
                'title': query.title(),
                'artist': 'YouTube Music',
                'success': True
            }
    except:
        pass
    
    return {'success': False}

# ==================== HANDLERS ====================
@bot.message_handler(commands=['start'])
def start(message):
    if not is_subscribed(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "🔥 **Premium Music Bot** 🔥\n\n"
            "📢 **Pehle Channel Join Karo** phir unlimited songs download karo!\n\n"
            "✅ Join karne ke baad **/start** type karo!",
            reply_markup=get_subscribe_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    welcome_msg = """
🎵 **Welcome to Premium Music Bot!** 🎵

🔥 **Commands:**
`/kesariya` - Arijit Singh hit
`/tumbbad` - Horror theme
`/arijit` - All Arijit songs
`Any song name` - Direct search!

**Quality:** 320kbps Premium 🎧
**No Limits!** Unlimited downloads
    """
    bot.send_message(message.chat.id, welcome_msg, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    if is_subscribed(call.from_user.id):
        bot.edit_message_text(
            "✅ **Subscribed!** Ab music download kar sakte ho!\n\n"
            "🎵 **/start** type karo!",
            call.message.chat.id,
            call.message.id,
            parse_mode='Markdown'
        )
    else:
        bot.answer_callback_query("❌ Abhi bhi join nahi kiya! 😠", show_alert=True)

@bot.message_handler(func=lambda m: True)
def handle_music(message):
    # Subscribe check
    if not is_subscribed(message.from_user.id):
        bot.reply_to(message, 
            "🚫 **Subscribe first!**\n📢 Channel join karo phir enjoy karo!",
            reply_markup=get_subscribe_keyboard(),
            parse_mode='Markdown'
        )
        return
    
    query = message.text.strip()
    status_msg = bot.reply_to(message, "🔍 **Searching Premium Songs...**")
    
    # Search music
    result = search_music(query)
    
    if not result['success']:
        bot.edit_message_text(
            "❌ **No results found!**\n\n"
            "Try: `kesariya`, `arijit`, `tumbbad`\n"
            "Ya exact song name type karo!",
            status_msg.chat.id,
            status_msg.id,
            parse_mode='Markdown'
        )
        return
    
    # Download & Send
    try:
        bot.edit_message_text("⬇️ **Downloading 320kbps Premium...**", status_msg.chat.id, status_msg.id)
        
        filename = f"music_{int(time.time())}.mp3"
        resp = requests.get(result['url'], stream=True, timeout=30)
        
        with open(filename, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        caption = f"🎵 **{result['title']}**\n👤 **{result['artist']}**\n🔥 **Premium Quality**"
        
        with open(filename, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=caption,
                parse_mode='Markdown',
                title=result['title'],
                performer=result['artist']
            )
        
        # Cleanup
        os.remove(filename)
        bot.delete_message(status_msg.chat.id, status_msg.id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ **Download failed!**\nError: {str(e)[:50]}", status_msg.chat.id, status_msg.id)

# Admin broadcast
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Usage: /broadcast <message>")
        return
    
    for member in bot.get_chat_members(CHANNEL_ID):
        try:
            bot.send_message(member.user.id, args[1])
        except:
            pass
    bot.reply_to(message, "✅ Broadcast sent!")

# ==================== RUN BOT ====================
if __name__ == "__main__":
    print("🎉 **Premium Music Bot Started!** 🚀")
    print(f"Channel: {CHANNEL_ID}")
    bot.infinity_polling()
