import streamlit as st


def section_label(title, badge=None, badge_color=None):
    """badge_color is accepted for call-site backwards compatibility but
    ignored - every section badge renders in the single accent color so
    labels read as one consistent design system, not a different crayon
    color per section."""
    badge_html = f'<span class="badge">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div class="section-hdr">
        <span class="label">{title}</span>
        <div class="rule"></div>
        {badge_html}
    </div>
    """, unsafe_allow_html=True)


def render_tool_hero(icon, title, subtitle, accent):
    """Centered single-tool hero: tinted icon chip, accent-colored title,
    gray subtitle - used at the top of every tool page."""
    st.markdown(f"""
    <div class="tool-hero">
        <div class="icon-lg" style="background:{accent}26;color:{accent};">{icon}</div>
        <h1 style="color:{accent};">{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def render_hero(eyebrow, title_lines, subtitle):
    title_html = "<br/>".join(title_lines)
    st.markdown(f"""
    <div class="hero">
        <div class="eyebrow"><span class="dot"></span>{eyebrow}</div>
        <h1>{title_html}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def render_summary_bar(uploaded_files):
    file_pills = "".join(
        f'<span class="file-pill">{f.name}</span>'
        for f in uploaded_files
    )
    st.markdown(f"""
    <div class="summary-bar">
        <span class="count">{len(uploaded_files)} files</span>
        <div style="display:flex;flex-wrap:wrap;gap:0.35rem;">{file_pills}</div>
    </div>
    """, unsafe_allow_html=True)


def render_success_banner(text="Merge complete"):
    st.markdown(f"""
    <div class="success-banner">
        <span class="check">✓</span>
        <span class="msg">{text}</span>
        <span class="sub">·  Ready to download</span>
    </div>
    """, unsafe_allow_html=True)


def render_unmatched_ui(all_unmatched, key_prefix="map"):
    manual_maps = {}
    total = sum(len(p) for p in all_unmatched.values())
    with st.expander(f"Resolve {total} unmatched columns", expanded=False):
        st.markdown(
            '<span style="color:var(--eq-text-secondary);font-size:0.75rem;">'
            'Map file columns to reference columns or leave as null.</span>',
            unsafe_allow_html=True,
        )
        for unit_label, pairs in all_unmatched.items():
            st.markdown(
                f'<span style="font-size:0.75rem;font-weight:600;color:var(--eq-text);">{unit_label}</span>',
                unsafe_allow_html=True,
            )
            unit_map = {}
            for fc, rc_options in pairs:
                col_l, col_r = st.columns([1, 1])
                with col_l:
                    st.markdown(
                        f'<span style="font-size:0.72rem;color:var(--eq-text-muted);">Column:</span> '
                        f'<span style="font-size:0.75rem;font-weight:600;color:var(--eq-text);">{fc}</span>',
                        unsafe_allow_html=True,
                    )
                with col_r:
                    options = ["Leave as null"] + rc_options
                    match = st.selectbox(
                        f"{fc}", options=options,
                        index=1, key=f"{key_prefix}_{unit_label}_{fc}",
                        label_visibility="collapsed",
                    )
                if match != "Leave as null":
                    unit_map[fc] = match
            manual_maps[unit_label] = unit_map
    return manual_maps


def render_dropped_columns_warning(dropped_by_unit):
    """dropped_by_unit: {unit_label: [(file_col, ref_col), ...]}"""
    any_dropped = any(dropped_by_unit.values())
    if not any_dropped:
        return
    lines = []
    for unit_label, dropped in dropped_by_unit.items():
        for file_col, ref_col in dropped:
            lines.append(f"**{unit_label}**: column `{file_col}` collided with another column "
                         f"mapped to `{ref_col}` - its data was dropped (first-mapped column kept).")
    st.warning("Duplicate-column collision(s) detected during alignment:\n\n" + "\n\n".join(lines))


def render_dtype_mismatch_warning(mismatches):
    """mismatches: {column: [sorted dtype categories]}, from
    core.schema.detect_dtype_mismatches. Concatenating a numeric column from
    one file with a text column of the same name from another silently
    produces one column mixing real numbers and strings -- warn so it's
    visible instead of surfacing as broken sums/sorts/filters later."""
    if not mismatches:
        return
    lines = [f"`{col}`: {' vs '.join(cats)}" for col, cats in mismatches.items()]
    st.warning(
        "Column(s) hold different data types across files, so the merged column will "
        "mix them (e.g. real numbers alongside text) with no automatic conversion:\n\n"
        + "\n\n".join(lines)
    )
