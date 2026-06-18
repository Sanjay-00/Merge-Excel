import io

import pandas as pd
import streamlit as st

from components import (
    render_header,
    render_how_card,
    render_success_banner,
    render_summary_bar,
    render_unmatched_ui,
    section_label,
)
from styles import CSS
from utils import (
    align_to_schema,
    build_file_summary,
    get_sheet_names,
    get_unmatched_pairs,
    read_single_file,
    to_excel_bytes,
)

st.set_page_config(page_title="Excel Merger", page_icon="📑", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


# ── Cached helpers ───────────────────────────────────────────────────────────
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


# ── Header + Upload ──────────────────────────────────────────────────────────
render_header()

col_upload, col_info = st.columns([5, 2], gap="medium")

with col_info:
    render_how_card()

with col_upload:
    st.markdown('<p class="upload-label">Drop your Excel files here or click Upload</p>',
                unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "upload", type=["xlsx", "xls", "xlsb"],
        accept_multiple_files=True, label_visibility="collapsed",
    )
    sheet_col, reboot_col = st.columns([8, 1])
    with sheet_col:
        sheet_input = st.text_input(
            "Sheet name", value="", placeholder="Leave blank for first sheet",
            help="Default sheet for all files. Leave blank for first sheet.",
        )
    with reboot_col:
        st.markdown("<div style='height:1.65rem'></div>", unsafe_allow_html=True)
        if st.button("🔄", help="Clear cache and reboot"):
            st.cache_data.clear()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ── Summary bar ──────────────────────────────────────────────────────────────
if uploaded_files:
    render_summary_bar(uploaded_files)

if not uploaded_files:
    st.stop()

# ── Per-file sheet selection ─────────────────────────────────────────────────
default_sheet = sheet_input.strip() or 0

all_sheet_names = {}
for f in uploaded_files:
    all_sheet_names[f.name] = cached_sheet_names(f.getvalue(), f.name)

has_multi_sheets = any(len(sheets) > 1 for sheets in all_sheet_names.values())

file_sheet_map = {}
if has_multi_sheets:
    with st.expander("Sheet selection (per file)", expanded=False):
        sheet_cols = st.columns(min(len(uploaded_files), 3))
        for i, f in enumerate(uploaded_files):
            sheets = all_sheet_names[f.name]
            if len(sheets) <= 1:
                file_sheet_map[f.name] = 0
                continue
            default_idx = 0
            if isinstance(default_sheet, str) and default_sheet in sheets:
                default_idx = sheets.index(default_sheet)
            with sheet_cols[i % 3]:
                file_sheet_map[f.name] = st.selectbox(
                    f.name, options=sheets, index=default_idx, key=f"sheet_{f.name}",
                )
else:
    for f in uploaded_files:
        file_sheet_map[f.name] = default_sheet

# ── Read all files ───────────────────────────────────────────────────────────
file_data = {}
warnings = []
progress = st.progress(0, text="Analyzing files...")

for i, f in enumerate(uploaded_files):
    progress.progress(
        int((i + 1) / len(uploaded_files) * 100),
        text=f"Reading {f.name} ({i + 1} of {len(uploaded_files)})"
    )
    df, err = cached_read(f.getvalue(), f.name, file_sheet_map[f.name])
    file_data[f.name] = (df, err)

progress.empty()

# ── Reference file + Schema preview ──────────────────────────────────────────
col_ref, col_schema = st.columns([1, 1], gap="medium")

with col_ref:
    section_label("Reference File", "sets column schema", "#D97706")
    ref_name = st.selectbox(
        "ref", options=[f.name for f in uploaded_files], index=0,
        help="All other files are aligned to this file's columns.",
        label_visibility="collapsed",
    )

ref_idx = next(i for i, f in enumerate(uploaded_files) if f.name == ref_name)
ref_df, ref_err = file_data[ref_name]

if ref_err:
    st.error(f"Cannot read reference file: {ref_err}")
    st.stop()

reference_cols = list(ref_df.columns)

with col_schema:
    section_label("Schema Preview", f"{len(reference_cols)} columns", "#6366F1")
    with st.expander(f"{ref_name}", expanded=False):
        st.write(reference_cols)

current_sig = (tuple(f.name for f in uploaded_files), ref_name, str(file_sheet_map))
if st.session_state.get("last_file_sig") != current_sig:
    st.session_state["merge_done"] = False
    st.session_state["last_file_sig"] = current_sig

# ── File summary ─────────────────────────────────────────────────────────────
section_label("File Summary", f"{len(uploaded_files)} files", "#0EA5E9")

summaries = []
for f in uploaded_files:
    df, err = file_data[f.name]
    if err:
        summaries.append({
            "File": f.name, "Rows": "-", "Total Columns": "-",
            "Matched Columns": "-", "Missing Columns": "-", "Extra Columns (dropped)": "-",
        })
        warnings.append(f.name)
    else:
        summaries.append(build_file_summary(f.name, df, reference_cols))

for w in warnings:
    st.warning(f"Could not read **{w}**")

st.dataframe(pd.DataFrame(summaries), use_container_width=True, hide_index=True)

# ── Unmatched column resolution ──────────────────────────────────────────────
all_unmatched = {}
for f in uploaded_files:
    if f.name == ref_name:
        continue
    df, err = file_data[f.name]
    if err:
        continue
    pairs = get_unmatched_pairs(df, reference_cols)
    resolvable = []
    for fc, rc in pairs:
        if fc and rc:
            resolvable.append((fc, rc if isinstance(rc, list) else [rc]))
    if resolvable:
        all_unmatched[f.name] = resolvable

manual_maps = render_unmatched_ui(all_unmatched) if all_unmatched else {}

# ── Merge ────────────────────────────────────────────────────────────────────
if st.button("▶  Merge Files", type="primary", use_container_width=True):
    frames = []
    errors = []
    ordered_names = [ref_name] + [f.name for f in uploaded_files if f.name != ref_name]

    for name in ordered_names:
        df, err = file_data[name]
        if err:
            errors.append(f"{name}: {err}")
            continue
        if name == ref_name:
            frames.append(df)
        else:
            frames.append(align_to_schema(df, reference_cols, manual_maps.get(name)))

    if not frames:
        st.error("Merge failed, no valid data.")
        st.stop()

    merged_df = pd.concat(frames, ignore_index=True)
    merge_progress = st.progress(0, text="Generating Excel file...")

    def update_progress(written, total):
        pct = int(written / total * 100)
        merge_progress.progress(pct, text=f"Writing rows {written:,} of {total:,}")

    excel_bytes = to_excel_bytes(merged_df, progress_cb=update_progress)
    merge_progress.empty()

    st.session_state["merged_df"] = merged_df
    st.session_state["excel_bytes"] = excel_bytes
    st.session_state["merge_done"] = True
    st.session_state["merge_errors"] = errors

# ── Results ──────────────────────────────────────────────────────────────────
if st.session_state.get("merge_done"):
    merged_df = st.session_state["merged_df"]
    errors = st.session_state.get("merge_errors", [])

    k1, k2, k3, k4 = st.columns([1, 1, 1, 2])
    k1.metric("Total Rows", f"{len(merged_df):,}")
    k2.metric("Columns", len(merged_df.columns))
    k3.metric("Files Merged", len(uploaded_files) - len(errors))
    with k4:
        st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
        st.download_button(
            label="⬇️  Download merged_output.xlsx",
            data=st.session_state["excel_bytes"],
            file_name="merged_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    render_success_banner()

    with st.expander("Preview, first 100 rows", expanded=True):
        st.dataframe(merged_df.head(100), use_container_width=True, hide_index=True)
