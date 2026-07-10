import io
import zipfile

import pandas as pd
import streamlit as st

from core.diff import diff_columns, diff_rows
from core.excel_writer import to_excel_bytes
from core.session import cached_read, cached_sheet_names, ns_key
from ui.shared import render_success_banner, render_tool_hero, render_unmatched_ui, section_label

TOOL = "diff"


def _load_one(label, key_ns):
    st.markdown(
        f'<p style="font-size:0.8rem;font-weight:600;color:var(--eq-text);margin-bottom:0.4rem;">{label}</p>',
        unsafe_allow_html=True,
    )
    f = st.file_uploader(
        label, type=["xlsx", "xls", "xlsb"], accept_multiple_files=False,
        label_visibility="collapsed", key=ns_key(TOOL, f"{key_ns}_uploader"),
    )
    if not f:
        return None, None
    with st.spinner(f"Reading {f.name}..."):
        sheets = cached_sheet_names(f.getvalue(), f.name)
    sheet_choice = 0
    if len(sheets) > 1:
        sheet_choice = st.selectbox(f"{label} sheet", options=sheets, index=0, key=ns_key(TOOL, f"{key_ns}_sheet"))
    with st.spinner(f"Reading {f.name} data..."):
        df, err = cached_read(f.getvalue(), f.name, sheet_choice)
    if err:
        st.error(f"Cannot read {label}: {err}")
        return None, None
    return f.name, df


def render_diff_page():
    render_tool_hero("🔍", "Compare / Diff", "Schema-aware diff between two versions of a workbook", "#06B6D4")

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        name_a, df_a = _load_one("File A (base)", "a")
    with col_b:
        name_b, df_b = _load_one("File B (comparison)", "b")

    if df_a is None or df_b is None:
        st.stop()

    # ── Column-level diff ────────────────────────────────────────────────────
    with st.spinner("Comparing columns..."):
        result, normalized_b = diff_columns(df_a, df_b)

    section_label("Column Diff", f"{len(result['common'])} common", "#0EA5E9")
    c1, c2, c3 = st.columns(3)
    c1.metric("Added Columns", len(result["added"]))
    c2.metric("Removed Columns", len(result["removed"]))
    c3.metric("Common Columns", len(result["common"]))

    if result["added"]:
        st.markdown(f"**Added in B:** {', '.join(result['added'])}")
    if result["removed"]:
        st.markdown(f"**Removed from A:** {', '.join(result['removed'])}")

    # Anything still ambiguous after normalization - resolve or leave as add/remove
    resolvable = [(fc, rc) for fc, rc in result["unmatched_pairs"] if rc]
    manual_map = {}
    if resolvable:
        manual_maps = render_unmatched_ui({"File B": resolvable}, key_prefix=ns_key(TOOL, "map"))
        manual_map = manual_maps.get("File B", {})
        if manual_map:
            normalized_b = normalized_b.rename(columns=manual_map)
            cols_a_set, cols_b_set = set(df_a.columns), set(normalized_b.columns)
            result["common"] = sorted(cols_a_set & cols_b_set)
            result["added"] = sorted(cols_b_set - cols_a_set)
            result["removed"] = sorted(cols_a_set - cols_b_set)

    # ── Row-level diff (needs a user-designated key column) ──────────────────
    section_label("Row Diff", "requires a key column", "#D97706")
    key_columns = st.multiselect(
        "Key column(s) that uniquely identify a row (e.g. Employee ID, Order Number)",
        options=result["common"], key=ns_key(TOOL, "key_cols"),
    )

    if not key_columns:
        st.info("Select one or more key columns above to enable row-level diff.")
        st.stop()

    with st.spinner("Comparing rows by key column(s)..."):
        row_result = diff_rows(df_a, normalized_b, key_columns=key_columns, common_columns=result["common"])

    dup_a = row_result["duplicate_keys"]["A"]
    dup_b = row_result["duplicate_keys"]["B"]
    if dup_a or dup_b:
        st.warning(
            f"Key column(s) {', '.join(key_columns)} are not unique - "
            f"{len(dup_a)} duplicate key value(s) in File A, {len(dup_b)} in File B. "
            "Diff results for these rows may be unreliable."
        )

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Added Rows", len(row_result["added"]))
    r2.metric("Removed Rows", len(row_result["removed"]))
    r3.metric("Changed Rows", len(row_result["changed"]))
    r4.metric("Unchanged Rows", row_result["unchanged_count"])

    with st.expander("Added rows (only in File B)", expanded=False):
        st.dataframe(row_result["added"], use_container_width=True, hide_index=True)
    with st.expander("Removed rows (only in File A)", expanded=False):
        st.dataframe(row_result["removed"], use_container_width=True, hide_index=True)
    with st.expander("Changed rows", expanded=True):
        st.dataframe(row_result["changed"], use_container_width=True, hide_index=True)

    with st.spinner("Preparing diff report..."):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("added_rows.xlsx", to_excel_bytes(row_result["added"]))
            zf.writestr("removed_rows.xlsx", to_excel_bytes(row_result["removed"]))
            zf.writestr("changed_rows.xlsx", to_excel_bytes(row_result["changed"]))

    st.download_button(
        label="Download diff_report.zip",
        data=buf.getvalue(),
        file_name="diff_report.zip",
        mime="application/zip",
        use_container_width=True,
        key=ns_key(TOOL, "download_btn"),
    )
    render_success_banner("Diff complete")
