import streamlit as st
import requests
import lyricsgenius

# --- 🔐 API CONFIG ---
SOUNDSTAT_KEY = "k30pcad0uDQgsQeRzZCSDiXqNGHN-kyzgpFdJXJF3Uw"
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

# Initialize Genius
genius = lyricsgenius.Genius(GENIUS_TOKEN)

# --- 🎨 UI ENHANCEMENTS ---
st.set_page_config(page_title="Lyricist Web Pro", page_icon="🎵", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #1DB954; color: white; }
    .lyrics-box { background-color: #1e2129; padding: 20px; border-radius: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 🚀 ENGINE FUNCTIONS ---
def fetch_soundstat_metadata(query):
    # SoundStat API call with proper Token in Headers
    url = f"https://api.soundstat.me/v1/search?q={query}"
    headers = {"Authorization": f"Bearer {SOUNDSTAT_KEY}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def get_lyrics(title):
    try:
        song = genius.search_song(title)
        return song.lyrics if song else "Lyrics not found in database."
    except:
        return "Lyrics service temporarily unavailable."

# --- 📱 UI LAYOUT ---
st.title("🎧 Lyricist Advanced Web Engine")
st.caption("Powered by SoundStat Premium & Streamlit")

query = st.text_input("", placeholder="Search for a song, artist, or album...", label_visibility="collapsed")

if query:
    with st.spinner("⚡ Fetching Premium Metadata..."):
        # SoundStat se data nikalna
        data = fetch_soundstat_metadata(query)
        
        if data and 'results' in data:
            res = data['results'][0] # Pehla sabse relevant result
            title = res.get('title', query)
            artist = res.get('artist', 'Unknown Artist')
            thumb = res.get('thumbnail', 'https://graph.org/file/default-thumb.jpg')
            # Direct Premium Download Link from SoundStat
            download_url = res.get('download_url') 

            st.divider()
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image(thumb, use_container_width=True, caption=f"Album: {res.get('album', 'Single')}")
                st.write(f"👤 **Artist:** {artist}")
                
                if download_url:
                    st.audio(download_url)
                    st.markdown(f'<a href="{download_url}" download><button style="width:100%; height:40px; background-color:#1DB954; border:none; border-radius:10px; color:white; cursor:pointer;">📥 Download High-Quality MP3</button></a>', unsafe_allow_html=True)
                else:
                    st.error("Premium Stream not available for this track.")

            with col2:
                st.subheader(f"📜 Lyrics: {title}")
                lyrics_text = get_lyrics(f"{title} {artist}")
                st.markdown(f'<div class="lyrics-box">{lyrics_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

        else:
            st.warning("⚠️ SoundStat Premium couldn't find this. Trying Fallback...")
            # Fallback logic here if needed