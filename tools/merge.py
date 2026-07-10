import pandas as pd
import streamlit as st

from core.excel_writer import to_excel_bytes
from core.schema import align_to_schema, build_file_summary, detect_dtype_mismatches, get_unmatched_pairs
from core.session import cached_read, cached_sheet_names, ns_key
from ui.shared import (
    render_dropped_columns_warning,
    render_dtype_mismatch_warning,
    render_success_banner,
    render_summary_bar,
    render_tool_hero,
    render_unmatched_ui,
    section_label,
)

TOOL = "merge"


def render_merge_page():
    render_tool_hero("📑", "Merge Files", "Drop your Excel files · Get one consolidated master Excel file", "#6366F1")

    uploaded_files = st.file_uploader(
        "upload", type=["xlsx", "xls", "xlsb"],
        accept_multiple_files=True, label_visibility="collapsed",
        key=ns_key(TOOL, "uploader"),
    )

    # ── Summary bar ──────────────────────────────────────────────────────
    if uploaded_files:
        render_summary_bar(uploaded_files)

    if not uploaded_files:
        st.stop()

    # Files are tracked internally by name (file_data, sheet maps, session-state
    # widget keys) -- two uploads sharing a name would silently overwrite each
    # other with no visible error, since Streamlit's uploader doesn't prevent
    # duplicate filenames in one multi-upload.
    names = [f.name for f in uploaded_files]
    if len(names) != len(set(names)):
        duplicates = sorted({n for n in names if names.count(n) > 1})
        st.error(
            f"Two or more uploaded files share the same name ({', '.join(duplicates)}). "
            "Files are tracked by name, so duplicates would silently overwrite each "
            "other. Rename one of the files and re-upload."
        )
        st.stop()

    # ── Per-file sheet selection ──────────────────────────────────────────
    with st.spinner("Detecting sheets..."):
        all_sheet_names = {f.name: cached_sheet_names(f.getvalue(), f.name) for f in uploaded_files}

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
                with sheet_cols[i % 3]:
                    file_sheet_map[f.name] = st.selectbox(
                        f.name, options=sheets, index=0,
                        key=ns_key(TOOL, f"sheet_{f.name}"),
                    )
    else:
        for f in uploaded_files:
            file_sheet_map[f.name] = 0

    # ── Read all files ─────────────────────────────────────────────────────
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

    # ── Reference file + Schema preview ────────────────────────────────────
    col_ref, col_schema = st.columns([1, 1], gap="medium")

    with col_ref:
        section_label("Reference File", "sets column schema", "#D97706")
        ref_name = st.selectbox(
            "ref", options=[f.name for f in uploaded_files], index=0,
            help="All other files are aligned to this file's columns.",
            label_visibility="collapsed",
            key=ns_key(TOOL, "ref_name"),
        )

    ref_df, ref_err = file_data[ref_name]

    if ref_err:
        st.error(f"Cannot read reference file: {ref_err}")
        st.stop()

    reference_cols = list(ref_df.columns)

    if not reference_cols:
        # e.g. the chosen sheet is genuinely empty -- reindexing every other
        # file onto zero columns would silently produce a merged output with
        # rows but no columns at all, and no clue why.
        st.error(
            f"**{ref_name}** has no columns to align to (the sheet may be empty). "
            "Pick a different reference file or sheet."
        )
        st.stop()

    with col_schema:
        section_label("Schema Preview", f"{len(reference_cols)} columns", "#6366F1")
        with st.expander(f"{ref_name}", expanded=False):
            st.write(reference_cols)

    current_sig = (tuple(f.name for f in uploaded_files), ref_name, str(file_sheet_map))
    if st.session_state.get(ns_key(TOOL, "last_file_sig")) != current_sig:
        st.session_state[ns_key(TOOL, "merge_done")] = False
        st.session_state[ns_key(TOOL, "last_file_sig")] = current_sig

    # ── File summary ────────────────────────────────────────────────────────
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

    # ── Unmatched column resolution ─────────────────────────────────────────
    all_unmatched = {}
    for f in uploaded_files:
        if f.name == ref_name:
            continue
        df, err = file_data[f.name]
        if err:
            continue
        pairs = get_unmatched_pairs(df, reference_cols)
        resolvable = [(fc, rc) for fc, rc in pairs if rc]
        if resolvable:
            all_unmatched[f.name] = resolvable

    manual_maps = render_unmatched_ui(all_unmatched, key_prefix=ns_key(TOOL, "map")) if all_unmatched else {}

    # ── Merge ────────────────────────────────────────────────────────────────
    if st.button("Merge Files", type="primary", use_container_width=True, key=ns_key(TOOL, "merge_btn")):
        frames = []
        errors = []
        dropped_by_file = {}
        ordered_names = [ref_name] + [f.name for f in uploaded_files if f.name != ref_name]

        for name in ordered_names:
            df, err = file_data[name]
            if err:
                errors.append(f"{name}: {err}")
                continue
            if name == ref_name:
                frames.append(df)
            else:
                aligned_df, dropped = align_to_schema(df, reference_cols, manual_maps.get(name))
                frames.append(aligned_df)
                if dropped:
                    dropped_by_file[name] = dropped

        if not frames:
            st.error("Merge failed, no valid data.")
            st.stop()

        render_dropped_columns_warning(dropped_by_file)
        render_dtype_mismatch_warning(detect_dtype_mismatches(frames, reference_cols))
        merged_df = pd.concat(frames, ignore_index=True)
        merge_progress = st.progress(0, text="Generating Excel file...")

        def update_progress(written, total):
            pct = int(written / total * 100)
            merge_progress.progress(pct, text=f"Writing rows {written:,} of {total:,}")

        excel_bytes = to_excel_bytes(merged_df, progress_cb=update_progress)
        merge_progress.empty()

        st.session_state[ns_key(TOOL, "merged_df")] = merged_df
        st.session_state[ns_key(TOOL, "excel_bytes")] = excel_bytes
        st.session_state[ns_key(TOOL, "merge_done")] = True
        st.session_state[ns_key(TOOL, "merge_errors")] = errors

    # ── Results ──────────────────────────────────────────────────────────────
    if st.session_state.get(ns_key(TOOL, "merge_done")):
        merged_df = st.session_state[ns_key(TOOL, "merged_df")]
        errors = st.session_state.get(ns_key(TOOL, "merge_errors"), [])

        k1, k2, k3, k4 = st.columns([1, 1, 1, 2])
        k1.metric("Total Rows", f"{len(merged_df):,}")
        k2.metric("Columns", len(merged_df.columns))
        k3.metric("Files Merged", len(uploaded_files) - len(errors))
        with k4:
            st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
            st.download_button(
                label="Download merged_output.xlsx",
                data=st.session_state[ns_key(TOOL, "excel_bytes")],
                file_name="merged_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=ns_key(TOOL, "download_btn"),
            )

        render_success_banner()

        with st.expander("Preview, first 100 rows", expanded=True):
            st.dataframe(merged_df.head(100), use_container_width=True, hide_index=True)
