import streamlit as st

from core.pages import TOOL_PAGES
from ui.shared import render_hero

TOOL_ORDER = ["merge", "split", "concat", "diff", "trim", "reduce"]


def _render_tool_card(entry):
    # st.container(border=True) gives real DOM nesting (unlike opening/closing
    # a <div> across separate st.markdown calls, which the browser auto-closes
    # per call -- that produced an empty phantom box). core/styles.py targets
    # this testid directly (no :has()) since these 6 cards are currently the
    # only st.container() calls in the app; re-scope if that ever changes.
    with st.container(border=True):
        st.markdown(
            f'<div class="tool-card-icon" style="background:{entry["color"]}26;color:{entry["color"]};">'
            f'{entry["icon"]}</div>',
            unsafe_allow_html=True,
        )
        st.page_link(entry["page"], label=entry["page"].title, use_container_width=True)
        st.markdown(f'<div class="tool-card-desc">{entry["description"]}</div>', unsafe_allow_html=True)


def render_home_page():
    # Side gutter columns keep the hero + card grid from stretching edge to
    # edge of the (deliberately wide) block-container -- real Streamlit
    # columns, not a CSS max-width hack, so there's no risk of the container
    # ambiguity that caused the earlier "whole page in one box" bug.
    _, main_col, _ = st.columns([1, 16, 1])
    with main_col:
        render_hero(
            "Schema-aware Excel tools, runs on your machine",
            ["Your Excel Toolkit,", "Organized."],
            "Merge, split, diff, and clean Excel files - with a schema-aware matching engine "
            "that reconciles renamed and truncated headers instead of just concatenating blindly.",
        )

        row1 = st.columns(3, gap="medium")
        row2 = st.columns(3, gap="medium")
        for col, key in zip(row1 + row2, TOOL_ORDER):
            with col:
                _render_tool_card(TOOL_PAGES[key])
