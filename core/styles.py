CSS = """
<style>
:root {
    --eq-bg: #0B1120;
    --eq-surface: #111827;
    --eq-surface-2: #1E293B;
    --eq-border: #1F2937;
    --eq-border-strong: #334155;
    --eq-text: #F1F5F9;
    --eq-text-secondary: #94A3B8;
    --eq-text-muted: #64748B;
    --eq-accent: #6366F1;
    --eq-accent-hover: #4F46E5;
    --eq-accent-soft: rgba(99, 102, 241, 0.14);
    --eq-success: #10B981;
    --eq-success-hover: #059669;
    --eq-success-soft: rgba(16, 185, 129, 0.12);
    --eq-success-border: rgba(16, 185, 129, 0.35);
    --eq-warning: #F59E0B;
    --eq-danger: #F87171;
    --eq-radius: 10px;
}

#MainMenu, footer, header { visibility: hidden; }
.stApp { background: var(--eq-bg); }
body, .stApp, .stMarkdown, p, span, div, label, li { color: var(--eq-text); }
.block-container { padding: 1.75rem 3.5rem 2.5rem 3.5rem !important; max-width: 1400px; }

/* Streamlit auto-adds a heading-anchor link icon next to any real h1-h6 it
   detects, including our custom hero/section headings -- suppress it since
   these headings aren't meant to be individually link-shareable. */
[data-testid="stHeaderActionElements"] { display: none !important; }

h1, h2, h3, h4, h5, h6, p, span, div, label { letter-spacing: -0.005em; }

/* ── Tool page hero (centered icon + title + subtitle) ────────────────── */
.tool-hero {
    text-align: center;
    padding: 2rem 0 1.75rem 0;
}
.tool-hero .icon-lg {
    width: 4rem;
    height: 4rem;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.9rem;
    margin: 0 auto 1.25rem auto;
    animation: heroFadeInUp 0.5s ease both;
}
.tool-hero h1 {
    font-size: 1.9rem;
    font-weight: 800;
    margin: 0 0 0.6rem 0;
    letter-spacing: -0.02em;
    animation: heroFadeInUp 0.5s ease 0.05s both;
}
.tool-hero p {
    color: var(--eq-text-secondary);
    font-size: 0.95rem;
    max-width: 560px;
    margin: 0 auto;
    line-height: 1.5;
    animation: heroFadeInUp 0.5s ease 0.1s both;
}

.summary-bar {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    background: var(--eq-surface);
    border: 1px solid var(--eq-border);
    border-radius: var(--eq-radius);
    padding: 0.5rem 0.9rem;
    margin: 0.5rem 0 0 0;
    overflow: hidden;
}
.summary-bar .count {
    background: var(--eq-text);
    color: var(--eq-bg);
    border-radius: 20px;
    padding: 0.1rem 0.55rem;
    font-size: 0.68rem;
    font-weight: 700;
    white-space: nowrap;
    flex-shrink: 0;
}
.summary-bar .file-pill {
    background: var(--eq-surface-2);
    border: 1px solid var(--eq-border);
    border-radius: 6px;
    padding: 0.15rem 0.55rem;
    font-size: 0.7rem;
    color: var(--eq-text-secondary);
    white-space: nowrap;
}

/* ── Section labels ────────────────────────────────────────────────────── */
.section-hdr {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 1.1rem 0 0.45rem 0;
}
.section-hdr .label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--eq-text-secondary);
    white-space: nowrap;
}
.section-hdr .rule {
    flex: 1;
    height: 1px;
    background: var(--eq-border);
}
.section-hdr .badge {
    background: var(--eq-accent-soft);
    color: #A5B4FC;
    border-radius: 6px;
    padding: 0.1rem 0.55rem;
    font-size: 0.65rem;
    font-weight: 600;
    white-space: nowrap;
}

/* ── Success banner ────────────────────────────────────────────────────── */
.success-banner {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    background: var(--eq-success-soft);
    border: 1px solid var(--eq-success-border);
    border-radius: var(--eq-radius);
    padding: 0.55rem 0.9rem;
    margin: 0.5rem 0;
}
.success-banner .check {
    background: var(--eq-success);
    color: var(--eq-bg);
    border-radius: 50%;
    width: 1.2rem;
    height: 1.2rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.6rem;
    font-weight: 700;
    flex-shrink: 0;
}
.success-banner .msg { font-weight: 600; color: #6EE7B7; font-size: 0.82rem; }
.success-banner .sub { color: var(--eq-success); font-size: 0.72rem; }

/* ── Buttons ───────────────────────────────────────────────────────────── */
div[data-testid="stButton"] button[kind="primary"] {
    background: var(--eq-accent) !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    box-shadow: none !important;
    transition: background 0.15s ease !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background: var(--eq-accent-hover) !important;
}
div[data-testid="stButton"] button[kind="secondary"] {
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    background: var(--eq-surface) !important;
    color: var(--eq-text) !important;
    border-color: var(--eq-border-strong) !important;
}
div[data-testid="stDownloadButton"] button {
    background: var(--eq-success) !important;
    color: #06170F !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    box-shadow: none !important;
    transition: background 0.15s ease !important;
}
div[data-testid="stDownloadButton"] button:hover {
    background: var(--eq-success-hover) !important;
}

/* ── File uploader - large centered vertical dropzone ────────────────── */
[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: 1.5px dashed var(--eq-border-strong) !important;
    border-radius: 14px !important;
    padding: 1.25rem 1.5rem !important;
    min-height: 110px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--eq-accent) !important;
    background: var(--eq-accent-soft) !important;
    transform: translateY(-3px);
    box-shadow: 0 14px 28px -10px rgba(99, 102, 241, 0.3);
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    width: 100%;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    text-align: center !important;
    gap: 0.3rem !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] svg {
    display: block !important;
    width: 1.4rem !important;
    height: 1.4rem !important;
    margin: 0 auto 0.35rem auto !important;
    color: var(--eq-text-secondary) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span {
    display: block !important;
    color: var(--eq-text) !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small {
    display: block !important;
    color: var(--eq-text-secondary) !important;
    font-size: 0.78rem !important;
}
[data-testid="stFileUploaderDropzone"] button {
    margin: 0.7rem auto 0 auto !important;
    background: var(--eq-surface) !important;
    color: var(--eq-text) !important;
    border: 1px solid var(--eq-border-strong) !important;
    font-size: 0.78rem !important;
}
[data-testid="stFileUploaderFile"] { color: var(--eq-text) !important; }
[data-testid="stFileUploaderFileName"] { color: var(--eq-text) !important; }

/* ── Metrics ───────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--eq-surface) !important;
    border: 1px solid var(--eq-border) !important;
    border-radius: 8px !important;
    padding: 0.65rem 0.9rem !important;
    transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
    border-color: var(--eq-accent) !important;
    transform: translateY(-3px);
    box-shadow: 0 14px 28px -10px rgba(99, 102, 241, 0.3);
}
[data-testid="stMetricLabel"] {
    font-size: 0.66rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--eq-text-secondary) !important;
}
[data-testid="stMetricValue"] {
    color: var(--eq-text) !important;
}

[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
    font-size: 0.85rem !important;
    border-radius: 6px !important;
    background: var(--eq-surface-2) !important;
    color: var(--eq-text) !important;
    border-color: var(--eq-border) !important;
}
[data-testid="stTextInput"] input::placeholder {
    font-size: 0.82rem !important;
    color: var(--eq-text-muted) !important;
}
[data-baseweb="select"] > div {
    background: var(--eq-surface-2) !important;
    border-color: var(--eq-border) !important;
}
[data-baseweb="popover"] li { background: var(--eq-surface-2) !important; }

[data-testid="stExpander"] {
    border: 1px solid var(--eq-border) !important;
    border-radius: 8px !important;
    overflow: hidden;
    background: var(--eq-surface) !important;
    transition: border-color 0.2s ease;
}
[data-testid="stExpander"]:hover {
    border-color: var(--eq-accent) !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: var(--eq-text) !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--eq-border) !important;
    border-radius: 8px !important;
    overflow: hidden;
}

/* ── Sidebar ───────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--eq-surface) !important;
    border-right: 1px solid var(--eq-border) !important;
}
section[data-testid="stSidebar"] [data-testid="stLogo"] {
    height: 1.5rem !important;
    margin: 0.3rem 0 1.1rem 0.1rem;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] {
    margin-top: 2rem;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="secondary"] {
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: var(--eq-text-secondary) !important;
    border-color: var(--eq-border) !important;
    background: transparent !important;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: var(--eq-text-muted) !important;
    font-size: 0.72rem !important;
    text-align: center;
    margin-top: 0.6rem;
}

/* ── Sidebar nav (st.navigation) ──────────────────────────────────────── */
[data-testid="stSidebarNav"] {
    padding-top: 0.25rem !important;
}
[data-testid="stSidebarNavItems"] {
    gap: 0.15rem;
    max-height: none !important;
    height: auto !important;
    overflow: visible !important;
}
[data-testid="stSidebarNavViewButton"] {
    display: none !important;
}
/* Streamlit's sidebar nav link marks the active page via an internal
   "isActive" React prop, not a DOM attribute (confirmed: no aria-current,
   no stable class, anywhere in Streamlit's bundle) -- so the current page's
   own gray highlight is Streamlit's default and can't be retargeted with a
   plain attribute selector. :hover is a real, reliable pseudo-class though,
   so the interactive richness lives entirely there: a brightening border, a
   slide-right, and a soft glow shadow, matching the tool-card hover instead
   of a flat color swap. */
[data-testid="stSidebarNavLink"] {
    border-radius: 8px !important;
    color: var(--eq-text-secondary) !important;
    padding: 0.55rem 0.75rem !important;
    margin-bottom: 0.05rem !important;
    border-left: 2.5px solid transparent !important;
    transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stSidebarNavLink"] span {
    font-size: 0.88rem !important;
}
[data-testid="stSidebarNavLink"]:hover {
    background: var(--eq-accent-soft) !important;
    color: var(--eq-text) !important;
    border-left-color: var(--eq-accent) !important;
    transform: translateX(4px);
    box-shadow: 0 8px 20px -8px rgba(99, 102, 241, 0.45);
}
[data-testid="stSidebarNavSeparator"] { display: none !important; }

/* ── Home page hero + tool cards ──────────────────────────────────────── */
@keyframes heroFadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes dotPulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.55); }
    50% { box-shadow: 0 0 0 4px rgba(99, 102, 241, 0); }
}
.hero { text-align: center; padding: 1.5rem 0 2.25rem 0; }
.hero .eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: var(--eq-surface);
    border: 1px solid var(--eq-border);
    border-radius: 999px;
    padding: 0.35rem 0.9rem;
    font-size: 0.78rem;
    color: var(--eq-text-secondary);
    margin-bottom: 1.5rem;
    animation: heroFadeInUp 0.5s ease both;
}
.hero .eyebrow .dot {
    width: 6px; height: 6px; border-radius: 50%; background: var(--eq-accent);
    animation: dotPulse 2s ease-in-out infinite;
}
.hero h1 {
    font-size: 2.6rem;
    font-weight: 800;
    color: var(--eq-text);
    line-height: 1.15;
    letter-spacing: -0.02em;
    margin: 0 0 1rem 0;
    animation: heroFadeInUp 0.5s ease 0.05s both;
}
.hero p {
    font-size: 1rem;
    color: var(--eq-text-secondary);
    max-width: 640px;
    margin: 0 auto;
    line-height: 1.6;
    animation: heroFadeInUp 0.5s ease 0.1s both;
}

/* Tool tiles: real interactive boxes (border + background always visible),
   with a livelier hover state (accent border, lift, soft glow) and a subtle
   fade-in-up entrance so the grid feels alive on load rather than static.
   Each tile is a real st.container(border=True), which gives real DOM
   nesting for the st.page_link inside it (an earlier attempt tried to open
   and close a <div> across separate st.markdown calls, but each call is its
   own sanitized HTML fragment, so the browser silently auto-closed it and
   left a phantom empty box).

   IMPORTANT: every vertical block in Streamlit -- not just st.container(),
   also every st.columns() column -- shares this exact same
   "stVerticalBlockBorderWrapper" testid. A full DOM dump confirmed each card
   actually sits 3 levels deep: the outer gutter column, the per-card column,
   then our real st.container(border=True). A bare selector on the testid
   matches all three, which is why hovering a card also faintly lit up its
   two ancestor wrappers. The :has() chain below requires .tool-card-icon at
   an EXACT shallow depth that only the innermost, true card wrapper
   satisfies -- the two ancestor wrappers need many more hops to reach any
   icon, so they never match. If this structure changes in a future
   Streamlit version, re-verify with a DOM dump before adjusting the depth. */
@keyframes tileFadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(
    > div > div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] > div.stMarkdown > div[data-testid="stMarkdownContainer"] > div.tool-card-icon
) {
    border-radius: 12px !important;
    border-color: var(--eq-border) !important;
    min-height: 200px;
    padding-bottom: 0.5rem;
    display: flex !important;
    flex-direction: column;
    justify-content: flex-start;
    transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    /* fill-mode backwards (not both): holds the pre-animation state during
       the staggered animation-delay below so cards don't flash unstyled,
       but releases the transform property once the entrance finishes (its
       "to" keyframe is translateY(0), the same as unanimated). "both" was
       holding transform forever after entrance, at higher cascade priority
       than transitions, which silently killed the :hover lift below. */
    animation: tileFadeInUp 0.5s ease backwards;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(
    > div > div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] > div.stMarkdown > div[data-testid="stMarkdownContainer"] > div.tool-card-icon
):hover {
    border-color: var(--eq-accent) !important;
    transform: translateY(-4px);
    box-shadow: 0 14px 28px -10px rgba(99, 102, 241, 0.3);
}
[data-testid="stHorizontalBlock"] > div:nth-of-type(1) div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] > div.stMarkdown > div[data-testid="stMarkdownContainer"] > div.tool-card-icon) { animation-delay: 0.02s; }
[data-testid="stHorizontalBlock"] > div:nth-of-type(2) div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] > div.stMarkdown > div[data-testid="stMarkdownContainer"] > div.tool-card-icon) { animation-delay: 0.08s; }
[data-testid="stHorizontalBlock"] > div:nth-of-type(3) div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] > div.stMarkdown > div[data-testid="stMarkdownContainer"] > div.tool-card-icon) { animation-delay: 0.14s; }
.tool-card-icon {
    width: 2.6rem;
    height: 2.6rem;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    margin: 0.2rem 0 0.9rem 0;
    transition: transform 0.2s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(
    > div > div[data-testid="stVerticalBlock"] > div[data-testid="element-container"] > div.stMarkdown > div[data-testid="stMarkdownContainer"] > div.tool-card-icon
):hover .tool-card-icon {
    transform: scale(1.08) translateY(-1px);
}
[data-testid="stPageLink"] p {
    color: var(--eq-text) !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
}
.tool-card-desc, .tool-card-desc p {
    color: var(--eq-text-secondary) !important;
    font-size: 0.83rem;
    line-height: 1.5;
    margin-top: 0.35rem;
    padding-bottom: 0.75rem;
}
</style>
"""
