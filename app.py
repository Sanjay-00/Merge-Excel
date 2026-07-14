# onnxruntime (OCR backend for the PDF to Excel tool) must be imported
# before pandas on this platform: importing pandas first leaves onnxruntime's
# native DLL unable to initialize ("DLL load failed ... initialization
# routine failed"), verified on onnxruntime 1.22 and 1.27 on Windows. Loading
# it first costs nothing when unused and is a no-op if it isn't installed.
try:
    import onnxruntime  # noqa: F401
except ImportError:
    pass

import streamlit as st

from core.pages import EXTERNAL_TOOL_KEYS, TOOL_PAGES
from core.styles import CSS
from pages_registry import get_pages

st.set_page_config(page_title="DataForge", page_icon="assets/logo_icon.png", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.logo("assets/wordmark.png", icon_image="assets/logo_icon.png")

nav = st.navigation(get_pages())
nav.run()

with st.sidebar:
    # Hosted as their own separate apps, not this app's st.Page objects -
    # rendered as plain external links below the real nav, not mixed into it.
    for key in EXTERNAL_TOOL_KEYS:
        entry = TOOL_PAGES[key]
        st.page_link(entry["url"], label=entry["title"], icon=entry["icon"])
    if st.button("Reset everything", help="Clear cache and reset all tools", use_container_width=True):
        st.cache_data.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.caption("v1.0")
