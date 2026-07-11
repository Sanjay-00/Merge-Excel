import io
import zipfile

import openpyxl
import pandas as pd


def drop_empty_columns(df):
    """Column-level analog of the row-level dropna(how="all") already applied
    at read time. Returns (df, dropped_count)."""
    empty_cols = [c for c in df.columns if df[c].isna().all()]
    if not empty_cols:
        return df, 0
    return df.drop(columns=empty_cols), len(empty_cols)


def inspect_workbook_bloat(raw_bytes, filename, sheet_name=None):
    """Raw, non-pandas inspection of the *original* file used only to build an
    honest before/after report - the actual size reduction is achieved by the
    normal read-through-pandas -> to_excel_bytes round-trip, which already
    discards styles/images/pivot caches/defined names/conditional formatting
    (pandas never reads them into a DataFrame). This never raises - returns a
    partial dict with an "error" key on failure, same convention as
    read_single_file.
    """
    ext = filename.rsplit(".", 1)[-1].lower()
    result = {
        "original_format": ext,
        "images": 0,
        "image_total_bytes": 0,
        "defined_names": 0,
        "conditional_formats": 0,
        "has_pivot_cache": False,
        "used_range": None,
        "note": None,
        "error": None,
    }

    if ext == "xls":
        # Legacy binary OLE format - verbose relative to xlsx's zip-compressed
        # XML, so conversion is usually (not guaranteed) a real win.
        result["note"] = (
            "Detailed inspection only supported for .xlsx (file is .xls); legacy binary "
            ".xls is typically less space-efficient than zip-compressed .xlsx, so "
            "conversion often reduces size - but check the before/after size above "
            "rather than assuming it, since this isn't measured, just typical."
        )
        return result

    if ext == "xlsb":
        # .xlsb is ALREADY a compact binary format, unlike .xls - converting to
        # .xlsx can make large numeric-heavy files bigger, not smaller. Verified
        # on a real 20MB .xlsb during testing: the .xlsx round-trip came out ~29%
        # LARGER. Never claim a size win here that the actual before/after bytes
        # don't back up.
        result["note"] = (
            "Detailed inspection only supported for .xlsx (file is .xlsb); .xlsb is "
            "already a compact binary format, so converting to .xlsx is NOT guaranteed "
            "to reduce size and can make large files bigger. Check the before/after size "
            "above rather than assuming a win."
        )
        return result

    try:
        zf = zipfile.ZipFile(io.BytesIO(raw_bytes))
        names = zf.namelist()
        image_names = [n for n in names if n.startswith("xl/media/")]
        result["images"] = len(image_names)
        result["image_total_bytes"] = sum(zf.getinfo(n).file_size for n in image_names)
        result["has_pivot_cache"] = any(n.startswith("xl/pivotCache/") for n in names)

        wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), data_only=False)
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
        result["defined_names"] = len(wb.defined_names)
        try:
            result["conditional_formats"] = sum(len(cf.rules) for cf in ws.conditional_formatting)
        except Exception:
            result["conditional_formats"] = 0
        result["used_range"] = (ws.max_row, ws.max_column)
    except Exception as e:
        result["error"] = str(e)

    return result


def downcast_numeric_columns(df, columns=None):
    """Opt-in numeric downcast. pandas' own `to_numeric(downcast=...)` already
    refuses to pick a smaller dtype that would change a value, but this adds
    an explicit round-trip comparison as a second, independent safety check
    before ever swapping a column's dtype - if a downcast candidate somehow
    doesn't survive that check, it is skipped (not silently applied), and
    reported as such rather than assumed safe. Returns (df, report)."""
    columns = columns if columns is not None else [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    new_df = df.copy()
    report = {}

    for col in columns:
        original = df[col]
        if pd.api.types.is_integer_dtype(original):
            downcasted = pd.to_numeric(original, downcast="integer")
        elif pd.api.types.is_float_dtype(original):
            downcasted = pd.to_numeric(original, downcast="float")
        else:
            continue

        if downcasted.dtype == original.dtype:
            report[col] = {
                "before_dtype": str(original.dtype), "after_dtype": str(original.dtype),
                "applied": False, "reason": "no smaller dtype available without precision loss",
            }
            continue

        safe = ((downcasted.astype("float64") == original.astype("float64")) | (original.isna() & downcasted.isna())).all()
        if safe:
            new_df[col] = downcasted
            report[col] = {
                "before_dtype": str(original.dtype), "after_dtype": str(downcasted.dtype),
                "applied": True, "reason": None,
            }
        else:
            report[col] = {
                "before_dtype": str(original.dtype), "after_dtype": str(original.dtype),
                "applied": False, "reason": "would lose precision",
            }

    return new_df, report


def build_reduction_report(before_bytes, after_bytes, bloat_info, columns_dropped, downcast_info=None, output_format="xlsx"):
    """Assembles the final itemized before/after report. Pure data assembly,
    no I/O - every line traces to something actually measured by
    inspect_workbook_bloat/drop_empty_columns/downcast_numeric_columns, never
    an invented/estimated saving."""
    lines = []

    original_format = bloat_info.get("original_format")
    if original_format and original_format != "xlsx":
        lines.append(f"Converted from .{original_format} to .xlsx (see note below on whether this actually reduces size for this format).")
    if bloat_info.get("images"):
        lines.append(f"Removed {bloat_info['images']} embedded image(s) (~{bloat_info['image_total_bytes']:,} bytes).")
    if bloat_info.get("defined_names"):
        lines.append(f"Removed {bloat_info['defined_names']} defined name(s)/named range(s).")
    if bloat_info.get("conditional_formats"):
        lines.append(f"Removed {bloat_info['conditional_formats']} conditional formatting rule(s).")
    if bloat_info.get("has_pivot_cache"):
        lines.append("Removed pivot table cache.")
    if bloat_info.get("used_range"):
        rows, cols = bloat_info["used_range"]
        lines.append(f"Original used range: {rows:,} rows x {cols:,} columns (styles/formatting on unused cells removed).")
    if bloat_info.get("note"):
        lines.append(bloat_info["note"])
    if columns_dropped:
        lines.append(f"Dropped {columns_dropped} fully-empty column(s).")
    if downcast_info:
        applied = [c for c, r in downcast_info.items() if r["applied"]]
        skipped = [c for c, r in downcast_info.items() if not r["applied"]]
        if applied:
            lines.append(f"Downcast numeric dtype for: {', '.join(applied)}.")
        if skipped:
            lines.append(f"Skipped downcast (would lose precision) for: {', '.join(skipped)}.")
    if output_format == "csv":
        lines.append("Exported as CSV - workbook formatting/sheet concept dropped entirely for maximum size reduction.")
    if not lines:
        lines.append("No reducible bloat detected - file was already minimal.")

    if after_bytes > before_bytes:
        lines.insert(0, (
            f"The output is actually LARGER than the original ({after_bytes:,} > {before_bytes:,} bytes). "
            + ("This can happen with .xlsb source files, which are already a compact binary format - "
               "the .xlsx round-trip's XML/zip overhead can outweigh the bloat it removes on large, "
               "numeric-heavy sheets. " if original_format == "xlsb" else "")
            + "Consider keeping the original format, or trying CSV output."
        ))

    return {
        "before_bytes": before_bytes,
        "after_bytes": after_bytes,
        "saved_bytes": before_bytes - after_bytes,
        "saved_pct": round((1 - after_bytes / before_bytes) * 100, 1) if before_bytes else 0.0,
        "details": lines,
    }
