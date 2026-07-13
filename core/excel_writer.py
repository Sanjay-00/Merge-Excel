import io
import re

import pandas as pd

# Excel's hard per-sheet row limit (including the header row). ws.write()
# past this row returns an error code instead of raising, so without this
# guard rows would silently vanish from the output.
EXCEL_MAX_ROWS = 1_048_576

_WORKBOOK_OPTIONS = {
    "constant_memory": True,
    # Datetimes written without an explicit format render as raw serial
    # numbers (e.g. 45123) in Excel.
    "default_date_format": "yyyy-mm-dd",
    # A stray inf/-inf cell would otherwise raise deep inside ws.write();
    # this writes it as #NUM! instead.
    "nan_inf_to_errors": True,
}

# Excel forbids []:*?/\ in sheet names, 31 chars max, and blank names.
_SHEET_NAME_BAD_CHARS = re.compile(r"[\[\]:*?/\\]")


def safe_sheet_name(name, fallback="Sheet1"):
    name = _SHEET_NAME_BAD_CHARS.sub("_", str(name)).strip()
    return (name or fallback)[:31]


def _write_sheet(ws, df, progress_cb=None):
    for ci, col in enumerate(df.columns):
        ws.write(0, ci, str(col))

    total = len(df)
    chunk = 5000
    for start in range(0, total, chunk):
        end = min(start + chunk, total)
        for ri, row in enumerate(df.iloc[start:end].values.tolist()):
            for ci, val in enumerate(row):
                if pd.notna(val):
                    ws.write(start + ri + 1, ci, val)
        if progress_cb:
            progress_cb(end, total)


def _check_row_limit(df, label="Result"):
    if len(df) > EXCEL_MAX_ROWS - 1:
        raise ValueError(
            f"{label} has {len(df):,} rows, more than Excel's limit of "
            f"{EXCEL_MAX_ROWS - 1:,} data rows per sheet. Export as CSV instead."
        )


def to_excel_bytes(df, progress_cb=None, sheet_name="Merged"):
    import xlsxwriter

    _check_row_limit(df)
    buf = io.BytesIO()
    wb = xlsxwriter.Workbook(buf, _WORKBOOK_OPTIONS)
    _write_sheet(wb.add_worksheet(safe_sheet_name(sheet_name)), df, progress_cb)
    wb.close()
    return buf.getvalue()


def tables_to_excel_bytes(named_frames, progress_cb=None):
    """One workbook with one sheet per (name, df) pair. Sheet names are
    sanitized for Excel's rules and de-duplicated by numbering repeats.
    constant_memory mode is fine here because each sheet is written fully
    before the next one starts (never interleaved)."""
    import xlsxwriter

    for name, df in named_frames:
        _check_row_limit(df, label=f"Table '{name}'")

    buf = io.BytesIO()
    wb = xlsxwriter.Workbook(buf, _WORKBOOK_OPTIONS)
    used = {}
    total = len(named_frames)
    for i, (name, df) in enumerate(named_frames):
        base = safe_sheet_name(name)
        seen = used.get(base.lower(), 0)
        used[base.lower()] = seen + 1
        sheet = base if seen == 0 else safe_sheet_name(f"{base[:27]} ({seen + 1})")
        _write_sheet(wb.add_worksheet(sheet), df)
        if progress_cb:
            progress_cb(i + 1, total)
    wb.close()
    return buf.getvalue()
