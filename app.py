import pandas as pd
import streamlit as st

from utils import build_file_summary, merge_files, read_single_file, to_excel_bytes

st.set_page_config(page_title="Excel Merger", page_icon="📑", layout="wide")

st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem 4rem 3rem !important; }

/* ── Header ── */
.header-card {
    background: linear-gradient(135deg, #1a3660 0%, #2a6099 100%);
    border-radius: 14px;
    padding: 1.85rem 2.25rem;
    margin-bottom: 2rem;
}

/* ── Upload label ── */
.upload-label {
    color: #2563EB;
    font-size: 0.82rem;
    font-weight: 500;
    margin: 0 0 0.5rem 0;
}

/* ── How it works card ── */
.how-card {
    background: #ffffff;
    border: 1px solid #E5E7EB;
    border-left: 3px solid #2563EB;
    border-radius: 10px;
    padding: 1.25rem 1.4rem;
}

/* ── Summary bar ── */
.summary-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin: 1rem 0 0 0;
    overflow: hidden;
}

/* ── Section header ── */
.section-hdr {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 1.75rem 0 0.75rem 0;
}

/* ── Merge / Download buttons ── */
div[data-testid="stButton"] button[kind="primary"] {
    background-color: #2563EB !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.72rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    letter-spacing: 0.01em !important;
    transition: background 0.15s !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #1D4ED8 !important;
}
div[data-testid="stDownloadButton"] button {
    background-color: #2563EB !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    width: 100% !important;
}

/* ── Compact file uploader ── */
[data-testid="stFileUploaderDropzone"] {
    background: #F9FAFB !important;
    border: 1px solid #E5E7EB !important;
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
    color: #9CA3AF !important;
    font-size: 0.78rem !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #F9FAFB !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    padding: 1rem 1.25rem !important;
}

/* ── Sheet input placeholder ── */
[data-testid="stTextInput"] input {
    font-size: 0.78rem !important;
}
[data-testid="stTextInput"] input::placeholder {
    font-size: 0.78rem !important;
    color: #B0B8C4 !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def section_header(title, badge=None):
    badge_html = (
        f'<span style="background:#EFF6FF;color:#2563EB;border-radius:20px;'
        f'padding:0.1rem 0.6rem;font-size:0.68rem;font-weight:700;">{badge}</span>'
    ) if badge else ""
    st.markdown(f"""
    <div class="section-hdr">
        <span style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                     letter-spacing:0.1em;color:#9CA3AF;white-space:nowrap;">{title}</span>
        <div style="flex:1;height:1px;background:#F3F4F6;"></div>
        {badge_html}
    </div>
    """, unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-card">
    <div style="font-size:1.85rem;font-weight:800;color:white;letter-spacing:-0.02em;margin-bottom:0.4rem;">
        📑 Excel File Merger
    </div>
    <div style="color:rgba(255,255,255,0.55);font-size:0.88rem;font-weight:400;">
        Drop your Excel files to be merged &nbsp;·&nbsp; Get one consolidated master Excel file
    </div>
</div>
""", unsafe_allow_html=True)

# ── Two-column layout ─────────────────────────────────────────────────────────
left, right = st.columns([2, 1], gap="large")

with right:
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

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    sheet_input = st.text_input(
        "Sheet name",
        value="",
        placeholder="Leave blank for first sheet",
        help="Applied to all files. Leave blank to always read the first sheet.",
    )

with left:
    st.markdown('<p class="upload-label">Drop your Excel files here or click Upload</p>',
                unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "upload",
        type=["xlsx", "xls", "xlsb"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

# ── Summary bar ───────────────────────────────────────────────────────────────
if uploaded_files:
    names = ", ".join(f.name for f in uploaded_files)
    st.markdown(f"""
    <div class="summary-bar">
        <span style="background:#2563EB;color:white;border-radius:20px;padding:0.15rem 0.65rem;
                     font-size:0.72rem;font-weight:700;white-space:nowrap;flex-shrink:0;">
            {len(uploaded_files)} files
        </span>
        <span style="color:#6B7280;font-size:0.8rem;overflow:hidden;
                     text-overflow:ellipsis;white-space:nowrap;">{names}</span>
    </div>
    """, unsafe_allow_html=True)

if not uploaded_files:
    st.stop()

# ── Reference file selector ───────────────────────────────────────────────────
section_header("Reference File", "sets column schema")

ref_name = st.selectbox(
    "ref",
    options=[f.name for f in uploaded_files],
    index=0,
    help="All other files are aligned to this file's columns. Extra columns dropped, missing filled with blank.",
    label_visibility="collapsed",
)
ref_idx = next(i for i, f in enumerate(uploaded_files) if f.name == ref_name)

# Reset on change
current_sig = (tuple(f.name for f in uploaded_files), ref_name)
if st.session_state.get("last_file_sig") != current_sig:
    st.session_state["merge_done"] = False
    st.session_state["last_file_sig"] = current_sig

# ── Read reference ────────────────────────────────────────────────────────────
sheet_idx = sheet_input.strip() or 0
ref_file = uploaded_files[ref_idx]
ref_file.seek(0)

with st.spinner(f"Reading reference file: {ref_file.name}"):
    first_df, first_err = read_single_file(ref_file, sheet_idx)

if first_err:
    st.error(f"Cannot read reference file: {first_err}")
    st.stop()

reference_cols = list(first_df.columns)

with st.expander(f"Schema preview · {len(reference_cols)} columns · {ref_file.name}", expanded=False):
    st.write(reference_cols)

# ── File summary ──────────────────────────────────────────────────────────────
section_header("File Summary", f"{len(uploaded_files)} files")

summaries = []
warnings = []
progress = st.progress(0, text="Analyzing files...")

for i, f in enumerate(uploaded_files):
    progress.progress(
        int((i + 1) / len(uploaded_files) * 100),
        text=f"Reading {f.name} ({i + 1} of {len(uploaded_files)})"
    )
    if i == ref_idx:
        summaries.append(build_file_summary(f.name, first_df, reference_cols))
    else:
        f.seek(0)
        df, err = read_single_file(f, sheet_idx)
        if err:
            summaries.append({
                "File": f.name, "Rows": "-", "Total Columns": "-",
                "Matched Columns": "-", "Missing Columns": "-", "Extra Columns (dropped)": "-",
            })
            warnings.append(f.name)
        else:
            summaries.append(build_file_summary(f.name, df, reference_cols))

progress.empty()

for w in warnings:
    st.warning(f"Could not read **{w}**")

st.dataframe(pd.DataFrame(summaries), use_container_width=True, hide_index=True)

# ── Merge button ──────────────────────────────────────────────────────────────
st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

if st.button("▶  Merge Files", type="primary", use_container_width=True):
    ordered = [uploaded_files[ref_idx]] + [f for i, f in enumerate(uploaded_files) if i != ref_idx]
    for f in ordered:
        f.seek(0)
    with st.spinner("Merging..."):
        merged_df, _, errors = merge_files(ordered, sheet_input)
    for e in errors:
        st.warning(e)
    if merged_df is None:
        st.error("Merge failed - no valid data could be read from the uploaded files.")
        st.stop()
    st.session_state["merged_df"] = merged_df
    st.session_state["merge_done"] = True
    st.session_state["merge_errors"] = errors

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.get("merge_done"):
    merged_df = st.session_state["merged_df"]
    errors = st.session_state.get("merge_errors", [])

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.85rem;background:#F0FDF4;
                border:1px solid #BBF7D0;border-radius:10px;padding:0.9rem 1.25rem;
                margin:1rem 0;">
        <div style="background:#22C55E;color:white;border-radius:50%;width:1.6rem;height:1.6rem;
                    display:flex;align-items:center;justify-content:center;font-size:0.8rem;
                    font-weight:700;flex-shrink:0;">✓</div>
        <div>
            <div style="font-weight:700;color:#15803D;font-size:0.92rem;">Merge complete</div>
            <div style="color:#166534;font-size:0.78rem;margin-top:0.1rem;">
                Your master Excel file is ready to download below
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Rows", f"{len(merged_df):,}")
    c2.metric("Columns", len(merged_df.columns))
    c3.metric("Files Merged", len(uploaded_files) - len(errors))

    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

    with st.expander("Preview - first 100 rows", expanded=True):
        st.dataframe(merged_df.head(100), use_container_width=True, hide_index=True)

    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

    st.download_button(
        label="⬇️  Download merged_output.xlsx",
        data=to_excel_bytes(merged_df),
        file_name="merged_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
