import streamlit as st

from core.excel_writer import to_excel_bytes
from core.reduce_size import build_reduction_report, downcast_numeric_columns, drop_empty_columns, inspect_workbook_bloat
from core.session import cached_read, cached_sheet_names, ns_key
from ui.shared import render_success_banner, render_tool_hero, section_label

TOOL = "reduce"


def render_reduce_size_page():
    render_tool_hero("📉", "Reduce Size", "Shrink an Excel file with an honest before/after breakdown of what was removed", "#10B981")

    uploaded_file = st.file_uploader(
        "upload", type=["xlsx", "xls", "xlsb"],
        accept_multiple_files=False, label_visibility="collapsed",
        key=ns_key(TOOL, "uploader"),
    )

    if not uploaded_file:
        st.stop()

    raw_bytes = uploaded_file.getvalue()
    before_bytes = len(raw_bytes)

    with st.spinner(f"Reading {uploaded_file.name}..."):
        sheets = cached_sheet_names(raw_bytes, uploaded_file.name)

    sheet_choice = 0
    if len(sheets) > 1:
        sheet_choice = st.selectbox("Sheet", options=sheets, index=0, key=ns_key(TOOL, "sheet"))
    sheet_name_for_inspection = sheet_choice if isinstance(sheet_choice, str) else None

    with st.spinner("Reading sheet data..."):
        df, err = cached_read(raw_bytes, uploaded_file.name, sheet_choice)
    if err:
        st.error(f"Cannot read file: {err}")
        st.stop()

    with st.spinner("Inspecting original file for the before/after report..."):
        bloat_info = inspect_workbook_bloat(raw_bytes, uploaded_file.name, sheet_name=sheet_name_for_inspection)
    if bloat_info["error"]:
        st.warning(f"Could not fully inspect the original file for reporting purposes: {bloat_info['error']}")

    # ── Options ───────────────────────────────────────────────────────────────
    section_label("Reduction Options", None)
    opt1, opt2 = st.columns(2)
    with opt1:
        drop_empty = st.checkbox("Drop fully-empty columns", value=True, key=ns_key(TOOL, "drop_empty"))
        do_downcast = st.checkbox(
            "Downcast numeric dtypes (skips any column where it would lose precision)",
            value=False, key=ns_key(TOOL, "downcast"),
        )
    with opt2:
        output_format = st.radio(
            "Output format", options=["xlsx", "csv"], horizontal=True, key=ns_key(TOOL, "output_format"),
            help="CSV drops the workbook/sheet/formatting concept entirely for maximum size reduction.",
        )

    working_df = df
    columns_dropped = 0
    if drop_empty:
        with st.spinner("Dropping fully-empty columns..."):
            working_df, columns_dropped = drop_empty_columns(working_df)

    downcast_info = None
    if do_downcast:
        with st.spinner("Downcasting numeric columns (checking for precision loss)..."):
            working_df, downcast_info = downcast_numeric_columns(working_df)

    if output_format == "csv":
        with st.spinner("Writing CSV..."):
            output_bytes = working_df.to_csv(index=False).encode("utf-8")
        file_name = "reduced_output.csv"
        mime = "text/csv"
    else:
        write_progress = st.progress(0, text="Writing Excel file...")

        def update_progress(written, total):
            pct = int(written / total * 100)
            write_progress.progress(pct, text=f"Writing rows {written:,} of {total:,}")

        output_bytes = to_excel_bytes(working_df, progress_cb=update_progress)
        write_progress.empty()
        file_name = "reduced_output.xlsx"
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    after_bytes = len(output_bytes)
    report = build_reduction_report(before_bytes, after_bytes, bloat_info, columns_dropped, downcast_info, output_format)

    # ── Report ───────────────────────────────────────────────────────────────
    section_label("Before / After", f"{report['saved_pct']}% smaller", "#0EA5E9")
    m1, m2, m3 = st.columns(3)
    m1.metric("Original Size", f"{before_bytes / 1024:,.1f} KB")
    m2.metric("New Size", f"{after_bytes / 1024:,.1f} KB")
    m3.metric("Saved", f"{report['saved_bytes'] / 1024:,.1f} KB")

    st.markdown("**What changed and why:**")
    for line in report["details"]:
        st.markdown(f"- {line}")

    st.download_button(
        label=f"Download {file_name}",
        data=output_bytes,
        file_name=file_name,
        mime=mime,
        use_container_width=True,
        key=ns_key(TOOL, "download_btn"),
    )
    render_success_banner("Reduction complete")
