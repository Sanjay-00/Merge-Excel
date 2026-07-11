import streamlit as st

from tools.concat_sheets import render_concat_page
from tools.diff import render_diff_page
from tools.merge import render_merge_page
from tools.reduce_size import render_reduce_size_page
from tools.split import render_split_page
from tools.trim_columns import render_trim_page

# Centralized so pages_registry.py (st.navigation) and tools/home.py
# (st.page_link cards) reference identical page metadata - avoids a
# circular import (tools/home.py can't import from pages_registry.py,
# since pages_registry.py imports tools.home).
TOOL_PAGES = {
    "merge": {
        "page": st.Page(render_merge_page, title="Merge Files", icon="🧩", url_path="merge"),
        "icon": "📑",
        "color": "#6366F1",
        "description": "Combine multiple Excel files onto one reference schema, in seconds.",
    },
    "split": {
        "page": st.Page(render_split_page, title="Split by Column", icon="✂️", url_path="split"),
        "icon": "✂️",
        "color": "#8B5CF6",
        "description": "Split one Excel file into many, one output per distinct column value.",
    },
    "concat": {
        "page": st.Page(render_concat_page, title="Sheet-wise Concat", icon="📚", url_path="concat"),
        "icon": "📚",
        "color": "#3B82F6",
        "description": "Stack sheets from one or more workbooks into one consolidated file.",
    },
    "diff": {
        "page": st.Page(render_diff_page, title="Compare / Diff", icon="🔍", url_path="diff"),
        "icon": "🔍",
        "color": "#06B6D4",
        "description": "Schema-aware diff between two versions of a workbook.",
    },
    "trim": {
        "page": st.Page(render_trim_page, title="Trim Columns", icon="🧼", url_path="trim"),
        "icon": "🧼",
        "color": "#F59E0B",
        "description": "Clean up whitespace, invisible characters, and casing in specific columns.",
    },
    "reduce": {
        "page": st.Page(render_reduce_size_page, title="Reduce Size", icon="📉", url_path="reduce"),
        "icon": "📉",
        "color": "#10B981",
        "description": "Shrink an Excel file with an honest before/after breakdown of what was removed.",
    },
}
