import io
import os
import shutil

import pandas as pd

# The same split the mature extractors converged on (Camelot's lattice vs
# stream, Tabula's lattice vs stream): one engine for tables whose structure
# is drawn (ruling lines / cell borders, handles merged+spanning cells) and
# one for tables whose structure is implied by text alignment only.
#   auto  -> img2table (OpenCV line detection on a rendered page image,
#            duplicates spanned cells across their range, finds titles),
#            falling back to the pdfplumber strategies if it finds nothing
#   lines -> pdfplumber, columns/rows from vector ruling lines in the PDF
#   text  -> pdfplumber, columns/rows guessed from word-edge alignment
ENGINES = ("auto", "lines", "text")

_PDFPLUMBER_SETTINGS = {
    "lines": {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
    "text": {"vertical_strategy": "text", "horizontal_strategy": "text"},
}

# Tesseract is a system binary, not a pip package. The standard Windows
# installer (UB Mannheim build) does not add itself to PATH, so check its
# default locations too and patch PATH at runtime if found there.
_TESSERACT_WINDOWS_DIRS = [
    r"C:\Program Files\Tesseract-OCR",
    r"C:\Program Files (x86)\Tesseract-OCR",
]


def _tesseract_available():
    if shutil.which("tesseract"):
        return True
    for d in _TESSERACT_WINDOWS_DIRS:
        if os.path.isfile(os.path.join(d, "tesseract.exe")):
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
            return True
    return False


def ocr_backend():
    """Best available OCR backend name, or None.

    RapidOCR strongly preferred: tested head-to-head on a 300dpi scanned
    two-page table, RapidOCR read every cell correctly while Tesseract
    (any PSM mode) misread most digits and often lost the table entirely.
    Tesseract is kept only as a fallback when rapidocr isn't installed."""
    try:
        import rapidocr  # noqa: F401

        return "rapidocr"
    except ImportError:
        pass
    return "tesseract" if _tesseract_available() else None


def _clean_rows(raw_rows):
    rows = [
        ["" if pd.isna(c) else str(c).strip() for c in row]
        for row in raw_rows
    ]
    return [r for r in rows if any(c != "" for c in r)]


def _scan_text(pdf_bytes):
    """(page_count, has_any_text). has_any_text False on every page means the
    PDF is a scan/image (neither engine here does OCR), so the caller can
    explain *why* nothing was found instead of a bare "0 tables"."""
    import pdfplumber

    has_any_text = False
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            if (page.extract_text() or "").strip():
                has_any_text = True
                break
    return page_count, has_any_text


def _extract_with_pdfplumber(pdf_bytes, settings):
    import pdfplumber

    tables = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            for tno, raw in enumerate(page.extract_tables(settings)):
                rows = _clean_rows(raw)
                if rows:
                    tables.append({"page": pno, "index": tno, "rows": rows, "title": None})
    return tables


def _extract_with_img2table(pdf_bytes, use_ocr=False):
    from img2table.document import PDF

    ocr = None
    if use_ocr:
        if ocr_backend() == "rapidocr":
            from img2table.ocr.rapidocr import RapidOCR

            ocr = RapidOCR()
        else:
            from img2table.ocr import TesseractOCR

            ocr = TesseractOCR(n_threads=1, lang="eng")
    doc = PDF(pdf_bytes, detect_rotation=use_ocr, pdf_text_extraction=not use_ocr)
    extracted = doc.extract_tables(
        ocr=ocr, implicit_rows=False, implicit_columns=False, borderless_tables=True,
    )
    tables = []
    for pno, page_tables in extracted.items():
        for tno, t in enumerate(page_tables):
            # t.df's column labels are just 0..n ints; the real header text is
            # in the data rows, which keeps the "first row is header" option
            # behaving identically across engines.
            rows = _clean_rows(t.df.values.tolist())
            if rows:
                tables.append({"page": pno + 1, "index": tno, "rows": rows, "title": t.title})
    return tables


def extract_pdf_tables(pdf_bytes, engine="auto", use_ocr=False):
    """Extract every table found in a PDF.

    use_ocr=True renders pages to images and runs OCR on them instead of
    reading the text layer - the path for scanned/photographed PDFs. It
    requires an OCR backend (see ocr_backend()) and only the img2table
    engine supports it, so the engine argument is ignored.

    Returns (tables, page_count, has_any_text, error) - errors as values,
    same convention as core.io.read_single_file. tables is a list of dicts:
    {page (1-based), index (0-based within its page), rows (list of row
    lists; cells stringified and stripped, fully-empty rows dropped),
    title (str or None, only the img2table engine finds these)}.
    """
    try:
        page_count, has_any_text = _scan_text(pdf_bytes)

        if use_ocr:
            if ocr_backend() is None:
                return [], page_count, has_any_text, (
                    "OCR requested but no OCR backend is available. "
                    "Install one with: pip install rapidocr onnxruntime"
                )
            return _extract_with_img2table(pdf_bytes, use_ocr=True), page_count, has_any_text, None

        if engine in _PDFPLUMBER_SETTINGS:
            return _extract_with_pdfplumber(pdf_bytes, _PDFPLUMBER_SETTINGS[engine]), page_count, has_any_text, None

        # auto: grid detection first; it wins on merged/spanning cells and
        # multi-line headers. Only fall back when it finds nothing at all.
        try:
            tables = _extract_with_img2table(pdf_bytes)
        except Exception:
            tables = []
        if not tables:
            tables = _extract_with_pdfplumber(pdf_bytes, _PDFPLUMBER_SETTINGS["lines"])
        if not tables:
            tables = _extract_with_pdfplumber(pdf_bytes, _PDFPLUMBER_SETTINGS["text"])
        return tables, page_count, has_any_text, None
    except Exception as e:
        return [], 0, False, str(e)


def _unique_headers(header_cells):
    seen = {}
    cols = []
    for i, h in enumerate(header_cells):
        name = " ".join(str(h).split()) or f"Column {i + 1}"
        n = seen.get(name, 0)
        seen[name] = n + 1
        cols.append(name if n == 0 else f"{name} ({n + 1})")
    return cols


def rows_to_dataframe(rows, first_row_is_header):
    """Rows from extract_pdf_tables -> DataFrame. Rows are padded to the
    widest row first (merged/spanning PDF cells can yield ragged rows).
    Header cells are made non-empty and unique so downstream tools (which
    assume unique column labels) never see a duplicate header."""
    width = max(len(r) for r in rows)
    padded = [r + [""] * (width - len(r)) for r in rows]
    if first_row_is_header:
        return pd.DataFrame(padded[1:], columns=_unique_headers(padded[0]))
    return pd.DataFrame(padded, columns=[f"Column {i + 1}" for i in range(width)])


def coerce_numeric_columns(df):
    """Every cell arrives from PDF extraction as text. For each column where
    ALL non-blank cells parse as numbers (after stripping thousands commas),
    convert to a real numeric dtype so Excel receives numbers rather than
    number-shaped text. Mixed columns are left entirely as text - no partial
    per-cell coercion. Returns (new_df, converted_column_names)."""
    new_df = df.copy()
    converted = []
    for col in df.columns:
        s = df[col].replace("", pd.NA)
        if not s.notna().any():
            continue
        num = pd.to_numeric(s.str.replace(",", "", regex=False), errors="coerce")
        if num.notna().equals(s.notna()):
            new_df[col] = num
            converted.append(col)
    return new_df, converted


def stack_tables(dfs):
    """Positionally stack tables that are fragments of one logical table
    split across pages (the most common multi-page PDF report layout).
    All tables must have the same column count; the first table's headers
    win, and later fragments are renamed onto them by position.

    Returns (stacked_df, notes, error). error is set (and stacked_df None)
    when column counts differ, since positional stacking would silently
    misalign data in that case."""
    widths = {len(df.columns) for df in dfs}
    if len(widths) > 1:
        return None, [], (
            "Tables have different column counts "
            f"({', '.join(str(w) for w in sorted(widths))}), so they cannot be "
            "stacked positionally. Use one sheet per table instead."
        )

    base_cols = list(dfs[0].columns)
    notes = []
    aligned = [dfs[0]]
    for df in dfs[1:]:
        if list(df.columns) != base_cols:
            notes.append(
                "Some tables had different header text; the first table's "
                "headers were used for all of them (matched by position)."
            )
            df = df.set_axis(base_cols, axis=1)
        # A repeated header row inside the data (PDFs re-print the header on
        # every page even mid-table) would otherwise land in the output as a
        # data row of header text.
        if len(df):
            header_like = (df.astype(str) == [str(c) for c in base_cols]).all(axis=1)
            df = df[~header_like]
        aligned.append(df)
    if any(len(a) != len(d) for a, d in zip(aligned[1:], dfs[1:])):
        notes.append("Repeated header rows found inside later tables were dropped.")
    return pd.concat(aligned, ignore_index=True), sorted(set(notes)), None
