import pandas as pd

from core.dedupe import dedupe_columns


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
        # .str.strip() assumes string-dtype columns, which breaks on a fully
        # empty sheet (pandas gives it a numeric RangeIndex) or on numeric/
        # mixed-type headers - stringify every label first so this never
        # raises regardless of what pandas inferred for the header row.
        df.columns = [str(c).strip() for c in df.columns]
        df, _ = dedupe_columns(df)
        df.dropna(how="all", inplace=True)
        return df, None
    except Exception as e:
        return None, str(e)
