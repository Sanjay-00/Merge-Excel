CSS = """
<style>
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 3rem 2rem 3rem !important; }

.header-card {
    background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 60%, #6366f1 100%);
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1rem;
}
.upload-label {
    color: #1e3a5f;
    font-size: 0.8rem;
    font-weight: 600;
    margin: 0 0 0.35rem 0;
}
.how-card {
    background: #ffffff;
    border: 1px solid #E5E7EB;
    border-left: 3px solid #2563EB;
    border-radius: 10px;
    padding: 1.25rem 1.4rem;
    height: 100%;
}
.summary-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: #FFF7ED;
    border: 1px solid #FED7AA;
    border-radius: 8px;
    padding: 0.45rem 0.9rem;
    margin: 0.5rem 0 0 0;
    overflow: hidden;
}
.section-hdr {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0.6rem 0 0.3rem 0;
}

div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.65rem !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: opacity 0.15s !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    opacity: 0.9 !important;
}
div[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #059669 0%, #0d9488 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    width: 100% !important;
}
div[data-testid="stDownloadButton"] button:hover {
    opacity: 0.9 !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: #FAFBFF !important;
    border: 1px dashed #93C5FD !important;
    border-radius: 8px !important;
    padding: 0.4rem 0.75rem !important;
    min-height: unset !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] > div {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    gap: 0.75rem !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] svg { display: none !important; }
[data-testid="stFileUploaderDropzoneInstructions"] span { display: none !important; }
[data-testid="stFileUploaderDropzoneInstructions"] small {
    display: inline !important;
    color: #94A3B8 !important;
    font-size: 0.78rem !important;
}

[data-testid="stMetric"] {
    border-radius: 8px !important;
    padding: 0.6rem 0.8rem !important;
}
[data-testid="stMetric"]:nth-of-type(1) {
    background: #EFF6FF !important;
    border: 1px solid #BFDBFE !important;
}
[data-testid="stMetric"]:nth-of-type(2) {
    background: #F5F3FF !important;
    border: 1px solid #DDD6FE !important;
}
[data-testid="stMetric"]:nth-of-type(3) {
    background: #ECFDF5 !important;
    border: 1px solid #A7F3D0 !important;
}

[data-testid="stTextInput"] input {
    font-size: 0.78rem !important;
}
[data-testid="stTextInput"] input::placeholder {
    font-size: 0.78rem !important;
    color: #94A3B8 !important;
}

[data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    overflow: hidden;
}
</style>
"""
