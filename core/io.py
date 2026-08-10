import io
import re
import zipfile

import pandas as pd

from core.dedupe import dedupe_columns

# Some non-Excel exporters (e.g. loan/ERP report generators) emit an xlsx
# whose styles.xml has a self-closing <fill/> with no patternFill/gradientFill
# child. That's valid-looking XML but violates the schema openpyxl expects,
# so it raises TypeError: expected <class 'openpyxl.styles.fills.Fill'>
# instead of a readable parse error. Patch it in-place before handing the
# bytes to openpyxl/pandas.
_EMPTY_FILL_RE = re.compile(rb"<((?:\w+:)?)fill\s*/>")


def _repair_xlsx_bytes(raw):
    try:
        zin = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        return None
    if "xl/styles.xml" not in zin.namelist():
        return None
    styles = zin.read("xl/styles.xml")

    def repl(m):
        prefix = m.group(1)
        return b"<" + prefix + b'fill><' + prefix + b'patternFill patternType="none"/></' + prefix + b"fill>"

    patched = _EMPTY_FILL_RE.sub(repl, styles)
    if patched == styles:
        return None

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = patched if item.filename == "xl/styles.xml" else zin.read(item.filename)
            zout.writestr(item, data)
    return out.getvalue()


def _with_repair(uploaded_file, func, engine):
    try:
        return func(uploaded_file)
    except Exception:
        if engine != "openpyxl":
            raise
        raw = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
        repaired = _repair_xlsx_bytes(raw)
        if repaired is None:
            raise
        buf = io.BytesIO(repaired)
        buf.name = getattr(uploaded_file, "name", "")
        return func(buf)


def _get_engine(filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return {"xls": "xlrd", "xlsb": "pyxlsb"}.get(ext, "openpyxl")


def get_sheet_names(uploaded_file):
    try:
        engine = _get_engine(uploaded_file.name)
        xls = _with_repair(uploaded_file, lambda f: pd.ExcelFile(f, engine=engine), engine)
        return xls.sheet_names
    except Exception:
        return []


def read_single_file(uploaded_file, sheet_name_or_index):
    try:
        engine = _get_engine(uploaded_file.name)
        df = _with_repair(
            uploaded_file,
            lambda f: pd.read_excel(f, sheet_name=sheet_name_or_index, engine=engine),
            engine,
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
