import io
import re
import zipfile

import pandas as pd
import streamlit as st

from core.excel_writer import to_excel_bytes
from core.schema import similarity
from core.session import cached_read, cached_sheet_names, ns_key
from ui.shared import render_success_banner, render_tool_hero, section_label

TOOL = "split"
BLANK_LABEL = "(blank)"
FUZZY_THRESHOLD = 0.75
MAX_FUZZY_VALUES = 150
HIGH_CARDINALITY_WARNING_THRESHOLD = 100


def _safe_filename(value):
    name = str(value).strip() or "blank"
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name[:80] or "blank"


def _display_value(v):
    """Clean string form of a split-column value, used consistently for
    preview/grouping/filenames regardless of the column's dtype. A whole-number
    float (e.g. 5.0) displays as "5" -- pandas silently upcasts an int column
    to float64 the moment it has any blank cell, so a day-of-month column like
    [5, 10, None] would otherwise show as "5.0"/"10.0" everywhere. A "due date"
    column is just as plausibly a real date -- pandas reads it as a Timestamp,
    which would otherwise print the trivial "00:00:00" on every value even
    when no row actually has a time component."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, pd.Timestamp):
        if v.hour == 0 and v.minute == 0 and v.second == 0:
            return v.strftime("%Y-%m-%d")
        return v.strftime("%Y-%m-%d_%H-%M-%S")
    return str(v)


def _detect_case_variants(series):
    """Values that differ only by case or surrounding whitespace (e.g. "CHE"
    vs "che") would otherwise be silently split into separate output files.
    Returns {normalized_key: [distinct raw values]} for keys with more than
    one distinct raw value."""
    non_null = series.dropna().astype(str)
    if non_null.empty:
        return {}
    normalized = non_null.str.strip().str.casefold()
    variants = {}
    for norm_key, raw_group in non_null.groupby(normalized):
        distinct_raw = sorted(raw_group.unique())
        if len(distinct_raw) > 1:
            variants[norm_key] = distinct_raw
    return variants


def _build_canonical_map(series, variants):
    """Maps every raw value in a detected variant group to the most frequent
    raw spelling (by row count) in that group -- that spelling becomes the
    group's output filename and grouping key. Row data itself is untouched;
    only which output file a row lands in changes."""
    non_null = series.dropna().astype(str)
    normalized = non_null.str.strip().str.casefold()
    canonical = {}
    for norm_key, raw_group in non_null.groupby(normalized):
        if norm_key in variants:
            top_value = raw_group.value_counts().idxmax()
            for v in raw_group.unique():
                canonical[v] = top_value
    return canonical


def _find_fuzzy_candidates(values, threshold=FUZZY_THRESHOLD):
    """Pairs of already-distinct values (post case/whitespace fold) that are
    textually similar enough to plausibly be typos of each other -- e.g.
    "SAKIN" vs "SAKINN". Ranked by similarity, never auto-applied: unlike
    case-fold (provably the same value), textual similarity between short
    codes is a weak signal -- "CHE" vs "CHI" could be a typo or two
    genuinely different valid codes, so a human has to confirm each pair."""
    values = sorted(values)
    candidates = []
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            a, b = values[i], values[j]
            ratio = similarity(a, b)
            if ratio >= threshold:
                candidates.append((a, b, ratio))
    candidates.sort(key=lambda c: -c[2])
    return candidates


def _build_fuzzy_canonical_map(value_counts, approved_pairs):
    """Union-finds only the pairs a human explicitly approved, then maps
    every value in a merged group to the most frequent spelling (by row
    count) in that group."""
    parent = {v: v for v in value_counts.index}

    def find(v):
        while parent[v] != v:
            v = parent[v]
        return v

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a, b in approved_pairs:
        union(a, b)

    groups = {}
    for v in value_counts.index:
        groups.setdefault(find(v), []).append(v)

    canonical = {}
    for members in groups.values():
        if len(members) > 1:
            top_value = max(members, key=lambda v: value_counts[v])
            for v in members:
                canonical[v] = top_value
    return canonical


def render_split_page():
    render_tool_hero("✂️", "Split by Column Value", "Split one Excel file into many, one output per distinct column value", "#8B5CF6")

    uploaded_file = st.file_uploader(
        "upload", type=["xlsx", "xls", "xlsb"],
        accept_multiple_files=False, label_visibility="collapsed",
        key=ns_key(TOOL, "uploader"),
    )

    if not uploaded_file:
        st.stop()

    with st.spinner(f"Reading {uploaded_file.name}..."):
        sheets = cached_sheet_names(uploaded_file.getvalue(), uploaded_file.name)
    sheet_choice = 0
    if len(sheets) > 1:
        sheet_choice = st.selectbox("Sheet", options=sheets, index=0, key=ns_key(TOOL, "sheet"))

    with st.spinner("Reading sheet data..."):
        df, err = cached_read(uploaded_file.getvalue(), uploaded_file.name, sheet_choice)
    if err:
        st.error(f"Cannot read file: {err}")
        st.stop()

    section_label("Split Column", f"{len(df.columns)} columns available", "#D97706")
    split_col = st.selectbox(
        "col", options=list(df.columns), label_visibility="collapsed",
        key=ns_key(TOOL, "split_col"),
    )

    # ── Normalize to a clean string column first, regardless of dtype ─────
    # so numeric/date columns (e.g. a day-of-month "due date" column) go
    # through the same case-fold/fuzzy-typo pipeline as text columns instead
    # of crashing it (similarity() expects strings) or displaying "5.0"
    # instead of "5" (pandas upcasts int -> float64 the moment a column has
    # any blank cell).
    raw_col = df[split_col].map(_display_value, na_action="ignore")

    # ── Stage 1: case/whitespace variant detection (safe, auto-eligible) ──
    variants = _detect_case_variants(raw_col)

    merge_variants = False
    if variants:
        example_key, example_values = next(iter(variants.items()))
        example_text = " / ".join(f'"{v}"' for v in example_values)
        st.warning(
            f"Found {len(variants)} value(s) in **{split_col}** that differ only by case "
            f"or whitespace (e.g. {example_text}) - these will be split into separate "
            f"files unless merged below."
        )
        merge_variants = st.checkbox(
            "Merge values that differ only by case or whitespace into one output file each",
            value=False, key=ns_key(TOOL, "merge_variants"),
        )

    if merge_variants:
        canonical_map = _build_canonical_map(raw_col, variants)
        case_folded_col = raw_col.copy()
        mask = raw_col.notna()
        case_folded_col.loc[mask] = raw_col.loc[mask].astype(str).map(lambda v: canonical_map.get(v, v))
    else:
        case_folded_col = raw_col

    # ── Stage 2: fuzzy-typo suggestions (human-reviewed, never auto-applied) ──
    case_value_counts = case_folded_col.value_counts(dropna=True)
    distinct_values = list(case_value_counts.index)

    approved_pairs = []
    if len(distinct_values) > MAX_FUZZY_VALUES:
        st.info(
            f"Skipping typo-similarity check - {len(distinct_values)} distinct values "
            "is too many to compare pairwise."
        )
    elif len(distinct_values) > 1:
        candidates = _find_fuzzy_candidates(distinct_values)
        if candidates:
            section_label("Possible Typos", f"{len(candidates)} pair(s) found", "#D97706")
            st.markdown(
                '<span style="color:var(--eq-text-secondary);font-size:0.75rem;">'
                "These values look similar but are not identical after case/whitespace "
                "normalization. Tick any pair that is actually the same value to merge "
                "them - nothing is merged automatically.</span>",
                unsafe_allow_html=True,
            )
            for i, (a, b, ratio) in enumerate(candidates):
                checked = st.checkbox(
                    f'"{a}"  is the same as  "{b}"   ({ratio:.0%} similar)',
                    value=False, key=ns_key(TOOL, f"fuzzy_{i}"),
                )
                if checked:
                    approved_pairs.append((a, b))

    fuzzy_map = _build_fuzzy_canonical_map(case_value_counts, approved_pairs) if approved_pairs else {}
    effective_col = case_folded_col.map(lambda v: fuzzy_map.get(v, v), na_action="ignore") if fuzzy_map else case_folded_col

    current_sig = (uploaded_file.name, sheet_choice, split_col, merge_variants, tuple(sorted(approved_pairs)))
    if st.session_state.get(ns_key(TOOL, "last_sig")) != current_sig:
        st.session_state[ns_key(TOOL, "split_done")] = False
        st.session_state[ns_key(TOOL, "last_sig")] = current_sig

    # ── Per-value preview summary ────────────────────────────────────────
    value_counts = effective_col.value_counts(dropna=True)
    blank_count = int(effective_col.isna().sum())

    preview_rows = [{"Value": str(v), "Rows": int(c)} for v, c in value_counts.items()]
    if blank_count:
        preview_rows.append({"Value": BLANK_LABEL, "Rows": blank_count})

    section_label("Split Preview", f"{len(preview_rows)} output files", "#0EA5E9")
    if len(preview_rows) > HIGH_CARDINALITY_WARNING_THRESHOLD:
        st.warning(
            f"**{split_col}** has {len(preview_rows)} distinct values, so this will "
            f"produce {len(preview_rows)} output files. If you meant to split on a "
            "column with fewer, more meaningful groups (not a near-unique column like "
            "an ID), double-check your column choice before splitting."
        )
    st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

    if st.button("Split File", type="primary", use_container_width=True, key=ns_key(TOOL, "split_btn")):
        blank_mask = effective_col.isna()
        # groupby's dropna=False raises on some pandas versions when the column
        # has nulls (ValueError: Categorical categories cannot be null) - split
        # the blank rows out first and groupby only the non-null remainder.
        groups = list(df[~blank_mask].groupby(effective_col[~blank_mask]))
        if blank_mask.any():
            groups.append((BLANK_LABEL, df[blank_mask]))

        buf = io.BytesIO()
        split_progress = st.progress(0, text="Preparing output files...")
        used_names = {}
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, (value, group_df) in enumerate(groups):
                label = str(value)
                split_progress.progress(int((i + 1) / len(groups) * 100), text=f"Writing {label} ({i + 1} of {len(groups)})")
                base_name = _safe_filename(label)
                # two different raw values can sanitize to the same filename
                # (e.g. "A/B" and "A B" both become "A_B") -- number repeats
                # instead of silently overwriting one inside the zip.
                seen = used_names.get(base_name, 0)
                used_names[base_name] = seen + 1
                file_name = base_name if seen == 0 else f"{base_name}_{seen + 1}"
                excel_bytes = to_excel_bytes(group_df)
                zf.writestr(f"{file_name}.xlsx", excel_bytes)
        split_progress.empty()

        st.session_state[ns_key(TOOL, "zip_bytes")] = buf.getvalue()
        st.session_state[ns_key(TOOL, "split_done")] = True
        st.session_state[ns_key(TOOL, "split_summary")] = preview_rows

    if st.session_state.get(ns_key(TOOL, "split_done")):
        summary = st.session_state.get(ns_key(TOOL, "split_summary"), [])
        k1, k2 = st.columns([1, 3])
        k1.metric("Output Files", len(summary))
        with k2:
            st.markdown("<div style='height:0.85rem'></div>", unsafe_allow_html=True)
            st.download_button(
                label="Download split_output.zip",
                data=st.session_state[ns_key(TOOL, "zip_bytes")],
                file_name="split_output.zip",
                mime="application/zip",
                use_container_width=True,
                key=ns_key(TOOL, "download_btn"),
            )
        render_success_banner("Split complete")
