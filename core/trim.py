import re

import pandas as pd

ZERO_WIDTH_SPACE = "​"
ZERO_WIDTH_NON_JOINER = "‌"
ZERO_WIDTH_JOINER = "‍"
BOM = "﻿"
NBSP = "\xa0"

ZERO_WIDTH_CHARS = [ZERO_WIDTH_SPACE, ZERO_WIDTH_NON_JOINER, ZERO_WIDTH_JOINER, BOM]

DEFAULT_PUNCTUATION = ".,;:-–—'\"()[]"  # includes hyphen, en dash, em dash as literal strippable characters

_INVISIBLE_PREVIEW_MARKERS = {
    NBSP: "·",
    ZERO_WIDTH_SPACE: "[ZWSP]",
    ZERO_WIDTH_NON_JOINER: "[ZWNJ]",
    ZERO_WIDTH_JOINER: "[ZWJ]",
    BOM: "[BOM]",
}


def collapse_whitespace(series):
    def f(v):
        if not isinstance(v, str):
            return v
        return re.sub(r"\s+", " ", v.strip())
    return series.apply(f)


def strip_invisible_chars(series):
    def f(v):
        if not isinstance(v, str):
            return v
        for ch in ZERO_WIDTH_CHARS:
            v = v.replace(ch, "")
        return v.replace(NBSP, " ")
    return series.apply(f)


def strip_edge_punctuation(series, chars=DEFAULT_PUNCTUATION):
    def f(v):
        if not isinstance(v, str):
            return v
        return v.strip(chars)
    return series.apply(f)


def normalize_case(series, mode):
    def f(v):
        if not isinstance(v, str):
            return v
        if mode == "title":
            return v.title()
        if mode == "upper":
            return v.upper()
        if mode == "lower":
            return v.lower()
        return v
    return series.apply(f)


def _series_equal(a, b):
    both_na = a.isna() & b.isna()
    return (a == b) | both_na


def _is_string_like(series):
    return series.dtype == object or pd.api.types.is_string_dtype(series)


def apply_trim_operations(df, columns, operations, punctuation_chars=None, case_mode=None):
    """Apply the selected composable cleaning operations to `columns` of df.

    operations: subset of {"invisible", "whitespace", "punctuation", "case"},
    always applied in this fixed order regardless of selection order (invisible
    chars normalized to spaces before whitespace-collapse sweeps them up).

    Returns (new_df, change_report) where change_report is
    {column: {"changed": int, "newly_empty": int, "skipped_non_string": bool}}.
    """
    new_df = df.copy()
    change_report = {}

    for col in columns:
        original = df[col]
        if not _is_string_like(original):
            change_report[col] = {"changed": 0, "newly_empty": 0, "skipped_non_string": True}
            continue

        working = original
        if "invisible" in operations:
            working = strip_invisible_chars(working)
        if "whitespace" in operations:
            working = collapse_whitespace(working)
        if "punctuation" in operations and punctuation_chars:
            working = strip_edge_punctuation(working, punctuation_chars)
        if "case" in operations and case_mode:
            working = normalize_case(working, case_mode)

        new_df[col] = working
        changed_mask = ~_series_equal(original, working)
        was_nonempty_str = original.apply(lambda v: isinstance(v, str) and v != "")
        newly_empty_mask = was_nonempty_str & (working == "")

        change_report[col] = {
            "changed": int(changed_mask.sum()),
            "newly_empty": int(newly_empty_mask.sum()),
            "skipped_non_string": False,
        }

    return new_df, change_report


def _visualize_invisible(v):
    if not isinstance(v, str):
        return v
    for ch, marker in _INVISIBLE_PREVIEW_MARKERS.items():
        v = v.replace(ch, marker)
    return v


def build_trim_preview(original_df, new_df, columns, cap=50):
    """Sample of rows where any selected column changed, rendered with
    invisible characters made visible. Returns (preview_df, more_count)."""
    change_mask = pd.Series(False, index=original_df.index)
    for col in columns:
        change_mask = change_mask | ~_series_equal(original_df[col], new_df[col])

    changed_idx = original_df.index[change_mask]
    sample_idx = changed_idx[:cap]

    rows = []
    for idx in sample_idx:
        record = {}
        for col in columns:
            record[f"{col} (before)"] = _visualize_invisible(original_df.at[idx, col])
            record[f"{col} (after)"] = _visualize_invisible(new_df.at[idx, col])
        rows.append(record)

    preview_df = pd.DataFrame(rows)
    more = len(changed_idx) - len(sample_idx)
    return preview_df, more
