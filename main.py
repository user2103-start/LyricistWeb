import telebot
import requests
import os
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote

# ==================== CONFIG ====================
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"  # Direct hardcoded
CHANNEL_USERNAME = "JPgViOHx7bdlMDZl"  # Channel link se
ADMIN_ID = 6593129349  # Tera ID hardcoded

MUSIC_API = "https://free-music-api2.vercel.app"

bot = telebot.TeleBot(BOT_TOKEN)

# ==================== FORCE SUBSCRIBE CHECK ====================
def is_subscribed(user_id):
    try:
        # Invite link format use karenge
        chat_member = bot.get_chat_member(f"https://t.me/+{CHANNEL_USERNAME}", user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Subscribe check error: {e}")
        return False

def get_subscribe_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📢 Channel Join Karo", url=f"https://t.me/+{CHANNEL_USERNAME}"),
        InlineKeyboardButton("✅ Check Subscription", callback_data="check_sub")
    )
    return markup

# ==================== MUSIC SEARCH ====================
def search_music(query):
    status_msg = "🔍 **Searching...**"
    
    # API 1: Free Music API
    try:
        if any(x in query.lower() for x in ['arijit', 'kesariya']):
            url = f"{MUSIC_API}/album/arijitsingh"
        else:
            url = f"{MUSIC_API}/getSongs"
        
        resp = requests.get(url, timeout=15).json()
        
        if isinstance(resp, list) and resp:
            song = resp[0]
            dl_url = song.get('download_url') or song.get('audio_url') or song.get('url')
            if dl_url:
                return {
                    'url': dl_url,
                    'title': song.get('title', query),
                    'artist': song.get('artist', 'Premium'),
                    'success': True
                }
    except:
        pass
    
    # Fallback: Direct JioSaavn hidden (2026 working)
    try:
        search_url = f"https://www.jiosaavn.com/api.php?query={quote(query)}&type=song&_marker=0&_p=1"
        resp = requests.get(search_url).json()
        if resp.get('songs') and resp['songs']:
            song = resp['songs'][0]
            dl_url = song.get('download_url') or f"https://jiosaavn.com/song/{song['id']}"
            return {
                'url': dl_url,
                'title': song['title'],
                'artist': song['primary_artists'],
                'success': True
            }
    except:
        pass
    
    return {'success': False}

# ==================== HANDLERS ====================
@bot.message_handler(commands=['start'])
def start(message):
    welcome_msg = """
🎵 **Premium Music Bot Active!** 🎵

🔥 **Unlimited 320kbps Downloads:**
`/kesariya` - Arijit 🔥
`/arijit` - Full collection
`/tumbbad` - Horror hits
`Any song name`!

**Pehle Channel Join Karo!** 📢
    """
    
    if not is_subscribed(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "🚫 **Subscribe First!**\n\n" + welcome_msg,
            reply_markup=get_subscribe_keyboard(),
            parse_mode='Markdown'
        )
    else:
        bot.send_message(message.chat.id, welcome_msg, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub(call):
    if is_subscribed(call.from_user.id):
        bot.edit_message_text(
            "✅ **Subscribed Successfully!**\n\n"
            "🎵 **Ab songs download karo:**\n`/kesariya` ya koi bhi song name!",
            call.message.chat.id,
            call.message.id,
            parse_mode='Markdown'
        )
    else:
        bot.answer_callback_query("❌ **Channel join nahi kiya!** 😠", show_alert=True)

@bot.message_handler(func=lambda m: True)
def handle_query(message):
    user_id = message.from_user.id
    
    # Admin ko direct access
    if user_id == ADMIN_ID:
        process_music(message)
        return
    
    # Normal user - subscribe check
    if not is_subscribed(user_id):
        bot.reply_to(message, 
            "🚫 **Pehle Channel Join Karo!**\n"
            "📢 https://t.me/+JPgViOHx7bdlMDZl",
            reply_markup=get_subscribe_keyboard()
        )
        return
    
    process_music(message)

def process_music(message):
    query = message.text.strip()
    status_msg = bot.reply_to(message, "🔍 **Premium Songs Search...**")
    
    result = search_music(query)
    
    if not result['success']:
        bot.edit_message_text(
            f"❌ **'{query}' nahi mila!**\n\n"
            "🔥 Try these:\n"
            "`kesariya`\n`arijit`\n`kal ho naa ho`\n"
            "`tumbbad`\n`bhakti songs`",
            status_msg.chat.id,
            status_msg.id,
            parse_mode='Markdown'
        )
        return
    
    try:
        bot.edit_message_text("⬇️ **320kbps Premium Download...**", status_msg.chat.id, status_msg.id)
        
        filename = f"music_{int(time.time())}.mp3"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        resp = requests.get(result['url'], headers=headers, stream=True, timeout=45)
        resp.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        
        caption = f"🎵 **{result['title']}**\n👤 **{result['artist']}**\n🔥 **Premium Quality**"
        
        with open(filename, 'rb') as audio_file:
            bot.send_audio(
                message.chat.id,
                audio_file,
                caption=caption,
                parse_mode='Markdown',
                title=result['title'],
                performer=result['artist'],
                thumb=None
            )
        
        os.remove(filename)
        bot.delete_message(status_msg.chat.id, status_msg.id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ **Download Error!**\n```{str(e)[:100]}```", status_msg.chat.id, status_msg.id, parse_mode='Markdown')

print("🎉 **Music Bot LIVE!** 🚀")
bot.infinity_polling()
