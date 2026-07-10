import io

import streamlit as st

from core.io import get_sheet_names, read_single_file


def ns_key(tool_name, key):
    return f"{tool_name}__{key}"


@st.cache_data(show_spinner=False)
def cached_sheet_names(file_content, filename):
    buf = io.BytesIO(file_content)
    buf.name = filename
    return get_sheet_names(buf)


@st.cache_data(show_spinner=False)
def cached_read(file_content, filename, sheet_idx):
    buf = io.BytesIO(file_content)
    buf.name = filename
    return read_single_file(buf, sheet_idx)
