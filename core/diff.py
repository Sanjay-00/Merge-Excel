import pandas as pd

from core.schema import _normalize_columns, get_unmatched_pairs


def diff_columns(df_a, df_b):
    """Column-level diff. Aligns df_b's columns onto df_a's naming via the
    same _normalize_columns matcher used by Merge/Concat, so a truncated or
    renamed header is treated as the same column rather than a false
    added+removed pair.

    Returns (result, normalized_df_b) where result has keys:
      added, removed, common: sorted lists of column names
      unmatched_pairs: output of get_unmatched_pairs(normalized_df_b, cols_a) - columns still ambiguous after normalization, for manual resolution.
    """
    cols_a = list(df_a.columns)
    normalized_b = _normalize_columns(df_b, cols_a)
    cols_b = list(normalized_b.columns)

    set_a, set_b = set(cols_a), set(cols_b)
    result = {
        "added": sorted(set_b - set_a),
        "removed": sorted(set_a - set_b),
        "common": sorted(set_a & set_b),
        "unmatched_pairs": get_unmatched_pairs(normalized_b, cols_a),
    }
    return result, normalized_b


def _values_equal(x, y):
    """A plain x == y flags "100" (text) vs 100 (number) as a real change --
    a false positive that's very plausible in practice, since the same
    column can easily get exported as text in one file version and as a
    real number in another. Tolerate type-only differences: try numeric
    equality first, then a whitespace-stripped string comparison, before
    falling back to strict equality."""
    if pd.isna(x) and pd.isna(y):
        return True
    if x == y:
        return True
    try:
        return float(x) == float(y)
    except (TypeError, ValueError):
        pass
    return str(x).strip() == str(y).strip()


def diff_rows(df_a, df_b_normalized, key_columns, common_columns):
    """Row-level diff, matched by key_columns identity (not full-row hash or
    position). common_columns is the set of non-added/removed columns to
    compare for changes (already schema-aligned by diff_columns).

    Returns a dict:
      added: DataFrame of rows only in df_b (keyed columns + compare_cols)
      removed: DataFrame of rows only in df_a
      changed: DataFrame of rows present in both with >=1 differing column,
               with '_A'/'_B' suffixed compare columns and a 'Changed Columns' col
      unchanged_count: int
      duplicate_keys: {"A": [...], "B": [...]} - distinct key tuples that are
        not 1:1 within a file; diff results for these keys may be unreliable.
    """
    compare_cols = [c for c in common_columns if c not in key_columns]

    a = df_a[key_columns + compare_cols].copy()
    b = df_b_normalized[key_columns + compare_cols].copy()

    dup_a = a[a.duplicated(subset=key_columns, keep=False)][key_columns].drop_duplicates()
    dup_b = b[b.duplicated(subset=key_columns, keep=False)][key_columns].drop_duplicates()

    merged = a.merge(b, on=key_columns, how="outer", suffixes=("_A", "_B"), indicator=True)

    removed = merged[merged["_merge"] == "left_only"][key_columns + [f"{c}_A" for c in compare_cols]]
    added = merged[merged["_merge"] == "right_only"][key_columns + [f"{c}_B" for c in compare_cols]]
    both = merged[merged["_merge"] == "both"]

    changed_rows = []
    unchanged_count = 0
    for _, row in both.iterrows():
        diff_cols = [c for c in compare_cols if not _values_equal(row[f"{c}_A"], row[f"{c}_B"])]
        if diff_cols:
            record = row.to_dict()
            record["Changed Columns"] = ", ".join(diff_cols)
            changed_rows.append(record)
        else:
            unchanged_count += 1

    changed = pd.DataFrame(changed_rows) if changed_rows else pd.DataFrame(
        columns=list(both.columns) + ["Changed Columns"]
    )
    if "_merge" in changed.columns:
        changed = changed.drop(columns=["_merge"])

    return {
        "added": added.reset_index(drop=True),
        "removed": removed.reset_index(drop=True),
        "changed": changed.reset_index(drop=True),
        "unchanged_count": unchanged_count,
        "duplicate_keys": {
            "A": dup_a.values.tolist(),
            "B": dup_b.values.tolist(),
        },
    }
