import streamlit as st

from core.pages import TOOL_PAGES
from tools.home import render_home_page


def get_pages():
    home_page = st.Page(render_home_page, title="Home", icon="🏠", url_path="home", default=True)
    return [home_page] + [entry["page"] for entry in TOOL_PAGES.values() if "page" in entry]
