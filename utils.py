import io
import pandas as pd


def _get_engine(filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return {"xls": "xlrd", "xlsb": "pyxlsb"}.get(ext, "openpyxl")


def read_single_file(uploaded_file, sheet_name_or_index):
    try:
        engine = _get_engine(uploaded_file.name)
        df = pd.read_excel(
            uploaded_file,
            sheet_name=sheet_name_or_index,
            engine=engine,
            dtype=str,
        )
        df.columns = df.columns.str.strip()
        df.dropna(how="all", inplace=True)
        return df, None
    except Exception as e:
        return None, str(e)


def build_file_summary(filename, df, reference_cols):
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


def align_to_schema(df, reference_cols):
    return df.reindex(columns=reference_cols)


def merge_files(uploaded_files, sheet_input):
    sheet_name_or_index = sheet_input.strip() or 0

    first_file = uploaded_files[0]
    first_df, err = read_single_file(first_file, sheet_name_or_index)
    if err:
        return None, [], [f"{first_file.name}: {err}"]

    reference_cols = list(first_df.columns)
    frames = [first_df]
    summaries = [build_file_summary(first_file.name, first_df, reference_cols)]
    errors = []

    for f in uploaded_files[1:]:
        df, err = read_single_file(f, sheet_name_or_index)
        if err:
            errors.append(f"{f.name}: {err}")
            continue
        summaries.append(build_file_summary(f.name, df, reference_cols))
        frames.append(align_to_schema(df, reference_cols))

    if not frames:
        return None, summaries, errors

    merged = pd.concat(frames, ignore_index=True)
    return merged, summaries, errors


def to_excel_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Merged")
    return buf.getvalue()
