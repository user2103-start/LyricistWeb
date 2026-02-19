import streamlit as st
import requests
import lyricsgenius

# --- CONFIG ---
SOUNDSTAT_KEY = "k30pcad0uDQgsQeRzZCSDiXqNGHN-kyzgpFdJXJF3Uw"
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"

# Initialize Genius safely
try:
    genius = lyricsgenius.Genius(GENIUS_TOKEN)
except:
    genius = None

st.set_page_config(page_title="Lyricist Pro", page_icon="🎵")
st.title("🎵 Lyricist Web Engine")

query = st.text_input("Search for a song:", placeholder="e.g. Animal")

if query:
    with st.spinner("Searching..."):
        # SoundStat API call
        url = f"https://api.soundstat.me/v1/search?q={query}"
        headers = {"Authorization": f"Bearer {SOUNDSTAT_KEY}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            res = response.json()
            
            if res.get('results'):
                song_data = res['results'][0]
                st.image(song_data.get('thumbnail'), width=250)
                st.subheader(song_data.get('title'))
                
                # Download & Player
                st.audio(song_data.get('download_url'))
                st.markdown(f"### [📥 Download MP3]({song_data.get('download_url')})")
                
                # Lyrics
                if genius:
                    s = genius.search_song(query)
                    if s: 
                        st.markdown("### 📜 Lyrics")
                        st.text_area("", s.lyrics, height=300)
            else:
                st.error("No results found on SoundStat Premium.")
        except Exception as e:
            st.error(f"Engine Error: {e}")
