import pandas as pd
import streamlit as st

from core.excel_writer import to_excel_bytes
from core.schema import align_to_schema, build_file_summary, get_unmatched_pairs
from core.session import cached_read, cached_sheet_names, ns_key
from ui.shared import (
    render_dropped_columns_warning,
    render_success_banner,
    render_summary_bar,
    render_tool_hero,
    render_unmatched_ui,
    section_label,
)

TOOL = "concat"


def _unit_key(workbook_name, sheet_name):
    return f"{workbook_name} :: {sheet_name}"


def render_concat_page():
    render_tool_hero("📚", "Sheet-wise Concat", "Stack sheets from one or more workbooks into one consolidated file", "#3B82F6")

    uploaded_files = st.file_uploader(
        "upload", type=["xlsx", "xls", "xlsb"],
        accept_multiple_files=True, label_visibility="collapsed",
        key=ns_key(TOOL, "uploader"),
    )

    if uploaded_files:
        render_summary_bar(uploaded_files)

    if not uploaded_files:
        st.stop()

    # ── Per-workbook sheet selection (default: all sheets participate) ─────
    section_label("Sheets to include", "per workbook", "#D97706")
    participating = []  # list of (workbook_name, sheet_name, uploaded_file)
    sheet_cols = st.columns(min(len(uploaded_files), 3))
    with st.spinner("Detecting sheets..."):
        workbook_sheets = {f.name: cached_sheet_names(f.getvalue(), f.name) for f in uploaded_files}
    for i, f in enumerate(uploaded_files):
        sheets = workbook_sheets[f.name]
        with sheet_cols[i % 3]:
            chosen = st.multiselect(
                f.name, options=sheets, default=sheets,
                key=ns_key(TOOL, f"sheets_{f.name}"),
            )
        for s in chosen:
            participating.append((f.name, s, f))

    if not participating:
        st.warning("Select at least one sheet to continue.")
        st.stop()

    # ── Read every participating sheet ──────────────────────────────────────
    sheet_data = {}
    read_progress = st.progress(0, text="Reading sheets...")
    for i, (wb_name, sheet_name, f) in enumerate(participating):
        read_progress.progress(
            int((i + 1) / len(participating) * 100),
            text=f"Reading {wb_name} - {sheet_name} ({i + 1} of {len(participating)})",
        )
        df, err = cached_read(f.getvalue(), f.name, sheet_name)
        sheet_data[_unit_key(wb_name, sheet_name)] = (df, err)
    read_progress.empty()

    # ── Reference sheet + schema preview ─────────────────────────────────────
    unit_keys = [_unit_key(wb, s) for wb, s, _ in participating]

    col_ref, col_schema = st.columns([1, 1], gap="medium")
    with col_ref:
        section_label("Reference Sheet", "sets column schema", "#D97706")
        ref_key = st.selectbox(
            "ref", options=unit_keys, index=0,
            help="All other sheets are aligned to this sheet's columns.",
            label_visibility="collapsed",
            key=ns_key(TOOL, "ref_key"),
        )

    ref_df, ref_err = sheet_data[ref_key]
    if ref_err:
        st.error(f"Cannot read reference sheet: {ref_err}")
        st.stop()

    reference_cols = list(ref_df.columns)

    with col_schema:
        section_label("Schema Preview", f"{len(reference_cols)} columns", "#6366F1")
        with st.expander(ref_key, expanded=False):
            st.write(reference_cols)

    include_provenance = st.checkbox(
        "Add a source column (workbook + sheet each row came from)",
        value=True, key=ns_key(TOOL, "provenance"),
    )

    current_sig = (tuple(unit_keys), ref_key, include_provenance)
    if st.session_state.get(ns_key(TOOL, "last_sig")) != current_sig:
        st.session_state[ns_key(TOOL, "concat_done")] = False
        st.session_state[ns_key(TOOL, "last_sig")] = current_sig

    # ── Sheet summary ─────────────────────────────────────────────────────────
    section_label("Sheet Summary", f"{len(unit_keys)} sheets", "#0EA5E9")
    summaries = []
    warnings = []
    for key in unit_keys:
        df, err = sheet_data[key]
        if err:
            summaries.append({
                "Sheet": key, "Rows": "-", "Total Columns": "-",
                "Matched Columns": "-", "Missing Columns": "-", "Extra Columns (dropped)": "-",
            })
            warnings.append(key)
        else:
            row = build_file_summary(key, df, reference_cols)
            row["Sheet"] = row.pop("File")
            summaries.append(row)

    for w in warnings:
        st.warning(f"Could not read **{w}**")

    st.dataframe(pd.DataFrame(summaries), use_container_width=True, hide_index=True)

    # ── Unmatched column resolution ─────────────────────────────────────────
    all_unmatched = {}
    for key in unit_keys:
        if key == ref_key:
            continue
        df, err = sheet_data[key]
        if err:
            continue
        pairs = get_unmatched_pairs(df, reference_cols)
        resolvable = [(fc, rc) for fc, rc in pairs if rc]
        if resolvable:
            all_unmatched[key] = resolvable

    manual_maps = render_unmatched_ui(all_unmatched, key_prefix=ns_key(TOOL, "map")) if all_unmatched else {}

    # ── Concat ────────────────────────────────────────────────────────────────
    if st.button("Concat Sheets", type="primary", use_container_width=True, key=ns_key(TOOL, "concat_btn")):
        frames = []
        errors = []
        dropped_by_sheet = {}
        ordered_keys = [ref_key] + [k for k in unit_keys if k != ref_key]

        for key in ordered_keys:
            df, err = sheet_data[key]
            if err:
                errors.append(f"{key}: {err}")
                continue
            if key == ref_key:
                aligned_df = df.copy()
            else:
                aligned_df, dropped = align_to_schema(df, reference_cols, manual_maps.get(key))
                if dropped:
                    dropped_by_sheet[key] = dropped
            if include_provenance:
                aligned_df = aligned_df.copy()
                aligned_df["Source"] = key
            frames.append(aligned_df)

        if not frames:
            st.error("Concat failed, no valid data.")
            st.stop()

        render_dropped_columns_warning(dropped_by_sheet)
        concat_df = pd.concat(frames, ignore_index=True)
        concat_progress = st.progress(0, text="Generating Excel file...")

        def update_progress(written, total):
            pct = int(written / total * 100)
            concat_progress.progress(pct, text=f"Writing rows {written:,} of {total:,}")

        excel_bytes = to_excel_bytes(concat_df, progress_cb=update_progress)
        concat_progress.empty()

        st.session_state[ns_key(TOOL, "concat_df")] = concat_df
        st.session_state[ns_key(TOOL, "excel_bytes")] = excel_bytes
        st.session_state[ns_key(TOOL, "concat_done")] = True
        st.session_state[ns_key(TOOL, "concat_errors")] = errors

    # ── Results ──────────────────────────────────────────────────────────────
    if st.session_state.get(ns_key(TOOL, "concat_done")):
        concat_df = st.session_state[ns_key(TOOL, "concat_df")]
        errors = st.session_state.get(ns_key(TOOL, "concat_errors"), [])

        k1, k2, k3, k4 = st.columns([1, 1, 1, 2])
        k1.metric("Total Rows", f"{len(concat_df):,}")
        k2.metric("Columns", len(concat_df.columns))
        k3.metric("Sheets Concatenated", len(unit_keys) - len(errors))
        with k4:
            st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
            st.download_button(
                label="Download concatenated_output.xlsx",
                data=st.session_state[ns_key(TOOL, "excel_bytes")],
                file_name="concatenated_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=ns_key(TOOL, "download_btn"),
            )

        render_success_banner("Concat complete")

        with st.expander("Preview, first 100 rows", expanded=True):
            st.dataframe(concat_df.head(100), use_container_width=True, hide_index=True)
