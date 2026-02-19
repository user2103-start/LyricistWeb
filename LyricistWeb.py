import streamlit as st
import requests
import lyricsgenius

# --- CONFIG ---
SOUNDSTAT_KEY = "k30pcad0uDQgsQeRzZCSDiXqNGHN-kyzgpFdJXJF3Uw"
GENIUS_TOKEN = "w-XTArszGpAQaaLu-JlViwy1e-0rxx4dvwqQzOEtcmmpYndHm_nkFTvAB5BsY-ww"
genius = lyricsgenius.Genius(GENIUS_TOKEN)

st.set_page_config(page_title="Lyricist Pro", page_icon="🎵")

st.title("🎵 Lyricist Web Engine")

query = st.text_input("Search Song:")

if query:
    # SoundStat API call with Header
    url = f"https://api.soundstat.me/v1/search?q={query}"
    headers = {"Authorization": f"Bearer {SOUNDSTAT_KEY}"}
    
    try:
        res = requests.get(url, headers=headers).json()
        if res.get('results'):
            song_data = res['results'][0]
            st.image(song_data.get('thumbnail'), width=200)
            st.subheader(song_data.get('title'))
            
            # Lyrics
            s = genius.search_song(query)
            if s: st.text_area("Lyrics", s.lyrics, height=300)
            
            # Download link
            st.markdown(f"[📥 Download MP3]({song_data.get('download_url')})")
        else:
            st.error("No results found on SoundStat.")
    except Exception as e:
        st.error(f"Error: {e}")
