import streamlit as st


def section_label(title, badge=None, badge_color="#6366F1"):
    badge_html = (
        f'<span style="background:{badge_color}15;color:{badge_color};border-radius:20px;'
        f'padding:0.08rem 0.5rem;font-size:0.62rem;font-weight:700;">{badge}</span>'
    ) if badge else ""
    st.markdown(f"""
    <div class="section-hdr">
        <span style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                     letter-spacing:0.1em;color:#64748B;white-space:nowrap;">{title}</span>
        <div style="flex:1;height:1px;background:#F1F5F9;"></div>
        {badge_html}
    </div>
    """, unsafe_allow_html=True)


def render_header():
    st.markdown("""
    <div class="header-card">
        <div style="font-size:1.5rem;font-weight:800;color:white;letter-spacing:-0.02em;margin-bottom:0.15rem;">
            📑 Excel File Merger
        </div>
        <div style="color:rgba(255,255,255,0.4);font-size:0.8rem;">
            Drop your Excel files · Get one consolidated master Excel file
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_how_card():
    st.markdown("""
    <div class="how-card">
        <div style="font-size:0.82rem;font-weight:700;color:#111827;margin-bottom:1rem;
                    letter-spacing:-0.01em;">📋 How it works</div>
    """ + "".join([
        f"""<div style="display:flex;align-items:flex-start;gap:0.55rem;margin-bottom:0.6rem;">
            <div style="background:#EFF6FF;color:#2563EB;min-width:1.25rem;height:1.25rem;
                        border-radius:50%;display:flex;align-items:center;justify-content:center;
                        font-size:0.6rem;font-weight:700;margin-top:0.1rem;">{n}</div>
            <div style="color:#374151;font-size:0.82rem;line-height:1.5;">{text}</div>
        </div>"""
        for n, text in [
            (1, 'Upload one or more <span style="font-weight:700;color:#111827;">Excel files</span>'),
            (2, 'Pick the <span style="font-weight:700;color:#111827;">reference file</span> for column schema'),
            (3, 'Click <span style="font-weight:700;color:#111827;">Merge Files</span>'),
            (4, 'Download the <span style="font-weight:700;color:#111827;">master Excel file</span>'),
        ]
    ]) + """
    </div>
    """, unsafe_allow_html=True)


def render_summary_bar(uploaded_files):
    file_pills = "".join(
        f'<span style="background:#FFF;border:1px solid #FDBA74;border-radius:6px;'
        f'padding:0.15rem 0.5rem;font-size:0.7rem;color:#9A3412;white-space:nowrap;">{f.name}</span>'
        for f in uploaded_files
    )
    st.markdown(f"""
    <div class="summary-bar">
        <span style="background:#EA580C;color:white;border-radius:20px;padding:0.1rem 0.5rem;
                     font-size:0.68rem;font-weight:700;white-space:nowrap;flex-shrink:0;">
            {len(uploaded_files)} files
        </span>
        <div style="display:flex;flex-wrap:wrap;gap:0.35rem;">{file_pills}</div>
    </div>
    """, unsafe_allow_html=True)


def render_success_banner():
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;background:#F0FDF4;
                border:1px solid #BBF7D0;border-radius:8px;padding:0.5rem 0.9rem;
                margin:0.4rem 0;">
        <span style="background:#059669;color:white;border-radius:50%;width:1.2rem;height:1.2rem;
                    display:inline-flex;align-items:center;justify-content:center;font-size:0.6rem;
                    font-weight:700;flex-shrink:0;">✓</span>
        <span style="font-weight:600;color:#065F46;font-size:0.82rem;">Merge complete</span>
        <span style="color:#059669;font-size:0.72rem;">·  Ready to download</span>
    </div>
    """, unsafe_allow_html=True)


def render_unmatched_ui(all_unmatched):
    manual_maps = {}
    total = sum(len(p) for p in all_unmatched.values())
    with st.expander(f"Resolve {total} unmatched columns", expanded=False):
        st.markdown(
            '<span style="color:#64748B;font-size:0.75rem;">'
            'Map file columns to reference columns or leave as null.</span>',
            unsafe_allow_html=True,
        )
        for fname, pairs in all_unmatched.items():
            st.markdown(
                f'<span style="font-size:0.75rem;font-weight:600;color:#1e293b;">{fname}</span>',
                unsafe_allow_html=True,
            )
            file_map = {}
            for fc, rc_options in pairs:
                col_l, col_r = st.columns([1, 1])
                with col_l:
                    st.markdown(
                        f'<span style="font-size:0.72rem;color:#94A3B8;">File:</span> '
                        f'<span style="font-size:0.75rem;font-weight:600;">{fc}</span>',
                        unsafe_allow_html=True,
                    )
                with col_r:
                    options = ["Leave as null"] + rc_options
                    match = st.selectbox(
                        f"{fc}", options=options,
                        index=1, key=f"map_{fname}_{fc}",
                        label_visibility="collapsed",
                    )
                if match != "Leave as null":
                    file_map[fc] = match
            manual_maps[fname] = file_map
    return manual_maps
