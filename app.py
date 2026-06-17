import io

import pandas as pd
import streamlit as st

from utils import (
    align_to_schema,
    build_file_summary,
    get_sheet_names,
    get_unmatched_pairs,
    read_single_file,
    to_excel_bytes,
)

st.set_page_config(page_title="Excel Merger", page_icon="📑", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 3rem 2rem 3rem !important; }

.header-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 60%, #6366f1 100%);
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1rem;
}
.upload-label {
    color: #1e3a5f;
    font-size: 0.8rem;
    font-weight: 600;
    margin: 0 0 0.35rem 0;
}
.how-card {
    background: #ffffff;
    border: 1px solid #E5E7EB;
    border-left: 3px solid #2563EB;
    border-radius: 10px;
    padding: 1.25rem 1.4rem;
    height: 100%;
}
.summary-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: #FFF7ED;
    border: 1px solid #FED7AA;
    border-radius: 8px;
    padding: 0.45rem 0.9rem;
    margin: 0.5rem 0 0 0;
    overflow: hidden;
}
.section-hdr {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0.6rem 0 0.3rem 0;
}

div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.65rem !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: opacity 0.15s !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    opacity: 0.9 !important;
}
div[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #059669 0%, #0d9488 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    width: 100% !important;
}
div[data-testid="stDownloadButton"] button:hover {
    opacity: 0.9 !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: #FAFBFF !important;
    border: 1px dashed #93C5FD !important;
    border-radius: 8px !important;
    padding: 0.4rem 0.75rem !important;
    min-height: unset !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    gap: 0.75rem !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] svg { display: none !important; }
[data-testid="stFileUploaderDropzoneInstructions"] span { display: none !important; }
[data-testid="stFileUploaderDropzoneInstructions"] small {
    display: inline !important;
    color: #94A3B8 !important;
    font-size: 0.78rem !important;
}

[data-testid="stMetric"] {
    border-radius: 8px !important;
    padding: 0.6rem 0.8rem !important;
}
[data-testid="stMetric"]:nth-of-type(1) {
    background: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
}
[data-testid="stMetric"]:nth-of-type(2) {
    background: #F5F3FF !important;
    border: 1px solid #DDD6FE !important;
}
[data-testid="stMetric"]:nth-of-type(3) {
    background: #ECFDF5 !important;
    border: 1px solid #A7F3D0 !important;
}

[data-testid="stTextInput"] input {
    font-size: 0.78rem !important;
}
[data-testid="stTextInput"] input::placeholder {
    font-size: 0.78rem !important;
    color: #94A3B8 !important;
}

[data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)


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


def section_label(title, badge=None, badge_color="#6366F1"):
    badge_html = (
        f'<span style="background:{badge_color}15;color:{badge_color};border-radius:20px;'
        f'padding:0.08rem 0.5rem;font-size:0.62rem;font-weight:700;">{badge}</span>'
    ) if badge else ""
    st.markdown(f"""
    <div class="section-hdr">
        <span style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                     letter-spacing:0.1em;color:#64748B;white-space:nowrap;">{title}</span>
        <div style="flex:1;height:1px;background:#F1F5F9;"></div>
        {badge_html}
    </div>
    """, unsafe_allow_html=True)


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-card">
    <div style="font-size:1.5rem;font-weight:800;color:white;letter-spacing:-0.02em;margin-bottom:0.15rem;">
        📑 Excel File Merger
    </div>
    <div style="color:rgba(255,255,255,0.4);font-size:0.8rem;">
        Drop your Excel files · Get one consolidated master Excel file
    </div>
</div>
""", unsafe_allow_html=True)

# ── Row 1: Upload + How it works ─────────────────────────────────────────────
col_upload, col_info = st.columns([5, 2], gap="medium")

with col_info:
    st.markdown("""
    <div class="how-card">
        <div style="font-size:0.82rem;font-weight:700;color:#111827;margin-bottom:1rem;
                    letter-spacing:-0.01em;">📋 How it works</div>
    """ + "".join([
        f"""<div style="display:flex;align-items:flex-start;gap:0.55rem;margin-bottom:0.6rem;">
            <div style="background:#EFF6FF;color:#2563EB;min-width:1.25rem;height:1.25rem;
                        border-radius:50%;display:flex;align-items:center;justify-content:center;
                        font-size:0.6rem;font-weight:700;margin-top:0.1rem;">{n}</div>
            <div style="color:#374151;font-size:0.82rem;line-height:1.5;">{text}</div>
        </div>"""
        for n, text in [
            (1, 'Upload one or more <span style="font-weight:700;color:#111827;">Excel files</span>'),
            (2, 'Pick the <span style="font-weight:700;color:#111827;">reference file</span> for column schema'),
            (3, 'Click <span style="font-weight:700;color:#111827;">Merge Files</span>'),
            (4, 'Download the <span style="font-weight:700;color:#111827;">master Excel file</span>'),
        ]
    ]) + """
        <div style="border-top:1px solid #F3F4F6;margin:0.9rem 0 0.7rem 0;"></div>
        <div style="color:#93C5FD;font-size:0.72rem;">
            .xlsx &nbsp;·&nbsp; .xls &nbsp;·&nbsp; .xlsb &nbsp;·&nbsp; up to 200 MB per file
        </div>
    </div>
    """, unsafe_allow_html=True)

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
    names = ", ".join(f.name for f in uploaded_files)
    st.markdown(f"""
    <div class="summary-bar">
        <span style="background:#EA580C;color:white;border-radius:20px;padding:0.1rem 0.5rem;
                     font-size:0.68rem;font-weight:700;white-space:nowrap;flex-shrink:0;">
            {len(uploaded_files)} files
        </span>
        <span style="color:#9A3412;font-size:0.75rem;overflow:hidden;
                     text-overflow:ellipsis;white-space:nowrap;">{names}</span>
    </div>
    """, unsafe_allow_html=True)

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

# ── Row 2: Reference file + Schema preview ──────────────────────────────────
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

# ── File summary (full width) ────────────────────────────────────────────────
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
manual_maps = {}
all_unmatched = {}
for f in uploaded_files:
    if f.name == ref_name:
        continue
    df, err = file_data[f.name]
    if err:
        continue
    pairs = get_unmatched_pairs(df, reference_cols)
    positional = [(fc, rc) for fc, rc in pairs if fc and rc]
    if positional:
        all_unmatched[f.name] = positional

if all_unmatched:
    total = sum(len(p) for p in all_unmatched.values())
    with st.expander(f"Resolve {total} unmatched columns", expanded=False):
        st.markdown(
            '<span style="color:#64748B;font-size:0.75rem;">'
            'These columns are at the same position but have different names. '
            'Map them to the reference column or leave as null.</span>',
            unsafe_allow_html=True,
        )
        for fname, pairs in all_unmatched.items():
            st.markdown(
                f'<span style="font-size:0.75rem;font-weight:600;color:#1e293b;">{fname}</span>',
                unsafe_allow_html=True,
            )
            file_map = {}
            for fc, rc in pairs:
                col_l, col_r = st.columns([1, 1])
                with col_l:
                    st.markdown(
                        f'<span style="font-size:0.72rem;color:#94A3B8;">File:</span> '
                        f'<span style="font-size:0.75rem;font-weight:600;">{fc}</span>',
                        unsafe_allow_html=True,
                    )
                with col_r:
                    match = st.selectbox(
                        f"{fc}", options=["Leave as null", rc],
                        index=1, key=f"map_{fname}_{fc}",
                        label_visibility="collapsed",
                    )
                if match != "Leave as null":
                    file_map[fc] = match
            manual_maps[fname] = file_map

# ── Merge + KPIs + Download (below file summary) ────────────────────────────
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

# ── Results preview (full width) ────────────────────────────────────────────
if st.session_state.get("merge_done"):
    merged_df = st.session_state["merged_df"]

    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;background:#F0FDF4;
                border:1px solid #BBF7D0;border-radius:8px;padding:0.5rem 0.9rem;
                margin:0.4rem 0;">
        <span style="background:#059669;color:white;border-radius:50%;width:1.2rem;height:1.2rem;
                    display:inline-flex;align-items:center;justify-content:center;font-size:0.6rem;
                    font-weight:700;flex-shrink:0;">✓</span>
        <span style="font-weight:600;color:#065F46;font-size:0.82rem;">Merge complete</span>
        <span style="color:#059669;font-size:0.72rem;">·  Ready to download</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"Preview, first 100 rows", expanded=True):
        st.dataframe(merged_df.head(100), use_container_width=True, hide_index=True)
