import os
import cv2
import asyncio
import img2pdf
import threading
from flask import Flask
from pyrogram import Client, filters

# --- 🌐 WEB SERVER FOR RENDER ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Video-to-PDF Engine is Live! 📄"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- 🟢 CONFIG ---
API_ID = 38456866
API_HASH = "30a8f347f538733a1d57dae8cc458ddc"
BOT_TOKEN = "8454384380:AAEsXBAm3IrtW3Hf1--2mH3xAyhnan-J3lg"

app = Client("VidToPdfBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- 🛠️ PROCESSING LOGIC ---
def process_video_to_pdf(video_path, pdf_path):
    cam = cv2.VideoCapture(video_path)
    img_list = []
    count = 0
    
    # Har 3-4 second ka frame lega (approx every 100 frames)
    while True:
        ret, frame = cam.read()
        if not ret: break
        
        if count % 100 == 0:
            frame_name = f"f_{count}.jpg"
            # Gray scale for extreme compression
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Resize for smaller data footprint
            small = cv2.resize(gray, (640, 360))
            cv2.imwrite(frame_name, small, [cv2.IMWRITE_JPEG_QUALITY, 30])
            img_list.append(frame_name)
        count += 1
    
    cam.release()
    
    if img_list:
        with open(pdf_path, "wb") as f:
            f.write(img_list_to_pdf(img_list))
        for img in img_list: os.remove(img)
        return True
    return False

def img_list_to_pdf(img_list):
    return img2pdf.convert(img_list)

# --- 🤖 BOT COMMANDS ---
@app.on_message(filters.video | filters.document)
async def handle_video(client, message):
    # Agar document hai toh check karo video hai ya nahi
    if message.document and not message.document.mime_type.startswith("video/"):
        return

    m = await message.reply_text("📥 **Video mil gayi! Download aur Process kar raha hoon...**")
    
    video_path = await message.download()
    pdf_path = f"Note_{message.from_user.id}.pdf"
    
    try:
        await m.edit("📸 **Frames nikaal raha hoon (Compressed Mode)...**")
        success = process_video_to_pdf(video_path, pdf_path)
        
        if success:
            await message.reply_document(pdf_path, caption="✅ **Compressed PDF taiyaar hai!**")
        else:
            await m.edit("❌ Video process nahi ho payi.")
            
    except Exception as e:
        await m.edit(f"❌ Error: {str(e)[:50]}")
    
    finally:
        if os.path.exists(video_path): os.remove(video_path)
        if os.path.exists(pdf_path): os.remove(pdf_path)
        await m.delete()

# --- 🚀 RENDER RUNNER ---
async def start_bot():
    threading.Thread(target=run_web, daemon=True).start()
    await app.start()
    print("✅ Video-to-PDF Bot Started!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())
