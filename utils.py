import io
import pandas as pd


def _get_engine(filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return {"xls": "xlrd", "xlsb": "pyxlsb"}.get(ext, "openpyxl")


def get_sheet_names(uploaded_file):
    try:
        engine = _get_engine(uploaded_file.name)
        xls = pd.ExcelFile(uploaded_file, engine=engine)
        return xls.sheet_names
    except Exception:
        return []


def read_single_file(uploaded_file, sheet_name_or_index):
    try:
        engine = _get_engine(uploaded_file.name)
        df = pd.read_excel(
            uploaded_file,
            sheet_name=sheet_name_or_index,
            engine=engine,
        )
        df.columns = df.columns.str.strip()
        df.dropna(how="all", inplace=True)
        return df, None
    except Exception as e:
        return None, str(e)


def _is_truncated(short, long):
    s, l = short.lower(), long.lower()
    return len(s) >= 3 and l.startswith(s) and len(s) / len(l) > 0.5


def _normalize_columns(df, reference_cols):
    ref_set = set(reference_cols)
    rename_map = {}

    # Pass 1: case-insensitive name match
    ref_lower = {col.lower(): col for col in reference_cols}
    for col in df.columns:
        if col not in ref_set and col.lower() in ref_lower:
            rename_map[col] = ref_lower[col.lower()]

    # Pass 2: positional match for truncated column names
    exact_matches = set(df.columns) & ref_set
    matched_ref = exact_matches | set(rename_map.values())
    matched_file = exact_matches | set(rename_map.keys())
    if len(df.columns) >= len(reference_cols):
        for file_col, ref_col in zip(list(df.columns)[:len(reference_cols)], reference_cols):
            if file_col not in matched_file and ref_col not in matched_ref:
                shorter, longer = sorted([file_col, ref_col], key=len)
                if _is_truncated(shorter, longer):
                    rename_map[file_col] = ref_col
                    matched_ref.add(ref_col)
                    matched_file.add(file_col)

    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def build_file_summary(filename, df, reference_cols):
    df = _normalize_columns(df, reference_cols)
    ref_set = set(reference_cols)
    file_set = set(df.columns)
    return {
        "File": filename,
        "Rows": len(df),
        "Total Columns": len(df.columns),
        "Matched Columns": len(file_set & ref_set),
        "Missing Columns": len(ref_set - file_set),
        "Extra Columns (dropped)": len(file_set - ref_set),
    }


def get_unmatched_pairs(df, reference_cols):
    df = _normalize_columns(df, reference_cols)
    ref_set = set(reference_cols)
    exact_matches = set(df.columns) & ref_set
    unmatched_file = [c for c in df.columns if c not in exact_matches and not c.startswith("Unnamed")]
    unmatched_ref = [c for c in reference_cols if c not in exact_matches]
    pairs = []
    used_file = set()
    used_ref = set()

    if len(df.columns) >= len(reference_cols):
        for fc, rc in zip(list(df.columns)[:len(reference_cols)], reference_cols):
            if fc not in exact_matches and rc not in exact_matches:
                pairs.append((fc, rc))
                used_file.add(fc)
                used_ref.add(rc)

    remaining_file = [c for c in unmatched_file if c not in used_file]
    remaining_ref = [c for c in unmatched_ref if c not in used_ref]
    for fc in remaining_file:
        options = list(remaining_ref)
        if options:
            pairs.append((fc, options))
            remaining_ref = []
        else:
            pairs.append((fc, None))
    for rc in remaining_ref:
        pairs.append((None, rc))

    return pairs


def align_to_schema(df, reference_cols, manual_map=None):
    df = _normalize_columns(df, reference_cols)
    if manual_map:
        df = df.rename(columns=manual_map)
    return df.reindex(columns=reference_cols)



def to_excel_bytes(df, progress_cb=None):
    import xlsxwriter

    buf = io.BytesIO()
    wb = xlsxwriter.Workbook(buf, {"constant_memory": True})
    ws = wb.add_worksheet("Merged")

    for ci, col in enumerate(df.columns):
        ws.write(0, ci, col)

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

    wb.close()
    return buf.getvalue()
