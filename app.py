import streamlit as st

from core.styles import CSS
from pages_registry import get_pages

st.set_page_config(page_title="Excel Toolkit", page_icon="📑", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.logo("assets/wordmark.png", icon_image="assets/logo_icon.png")

nav = st.navigation(get_pages())
nav.run()

with st.sidebar:
    if st.button("Reset everything", help="Clear cache and reset all tools", use_container_width=True):
        st.cache_data.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.caption("v1.0 · runs locally, no data leaves your machine")
