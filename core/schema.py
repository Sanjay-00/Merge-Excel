from difflib import SequenceMatcher

from core.dedupe import duplicated_mask


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


def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def get_unmatched_pairs(df, reference_cols):
    df = _normalize_columns(df, reference_cols)
    ref_set = set(reference_cols)
    exact_matches = set(df.columns) & ref_set
    unmatched_file = [c for c in df.columns if c not in exact_matches and not c.startswith("Unnamed")]
    unmatched_ref = [c for c in reference_cols if c not in exact_matches]
    pairs = []
    for fc in unmatched_file:
        sorted_refs = sorted(unmatched_ref, key=lambda rc: similarity(fc, rc), reverse=True)
        pairs.append((fc, sorted_refs))
    return pairs


_DTYPE_CATEGORIES = {
    "i": "numeric", "u": "numeric", "f": "numeric",
    "O": "text", "b": "boolean", "M": "datetime", "m": "duration",
}


def detect_dtype_mismatches(frames, columns):
    """pd.concat silently combines a numeric column from one file with a text
    column of the same name from another into one inconsistent object column
    (e.g. real ints mixed with strings) -- no coercion, no warning. This scans
    the already schema-aligned frames and flags any column where more than
    one broad dtype category (numeric / text / boolean / datetime / duration)
    appears across files, so the merge tool can surface it instead of staying
    silent. int64-vs-float64 within "numeric" is NOT flagged -- that's a
    routine, harmless pandas quirk (a blank cell upcasts a column to float),
    not a real type conflict.
    """
    mismatches = {}
    for col in columns:
        categories = set()
        for frame in frames:
            if col not in frame.columns:
                continue
            non_null = frame[col].dropna()
            if non_null.empty:
                continue
            categories.add(_DTYPE_CATEGORIES.get(non_null.dtype.kind, non_null.dtype.kind))
        if len(categories) > 1:
            mismatches[col] = sorted(categories)
    return mismatches


def align_to_schema(df, reference_cols, manual_map=None):
    """Normalize df's columns onto reference_cols and reindex.

    Returns (aligned_df, dropped) where dropped is a list of
    (original_file_column, reference_column_it_collided_on) tuples for any
    column that had to be dropped because two source columns resolved to the
    same reference column (first occurrence wins, same as before - this is
    now just reported instead of silent).
    """
    original_cols = list(df.columns)
    df = _normalize_columns(df, reference_cols)
    if manual_map:
        df = df.rename(columns=manual_map)

    mask = duplicated_mask(df)
    dropped = [
        (original_cols[i], df.columns[i])
        for i in range(len(df.columns))
        if mask[i]
    ]
    df = df.loc[:, ~mask]
    return df.reindex(columns=reference_cols), dropped
