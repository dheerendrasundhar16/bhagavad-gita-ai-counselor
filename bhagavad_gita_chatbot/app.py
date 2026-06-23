import streamlit as st
import requests
import uuid
import os
import re
from typing import Dict, List, Optional

# --- Page Configuration ---
st.set_page_config(
    page_title="Bhagavad Gita AI Counselor",
    page_icon="🕉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constants ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

EMOTION_CARDS = [
    {"emoji": "😰", "label": "Anxiety",      "starter": "I'm feeling overwhelmed with anxiety and can't calm my mind"},
    {"emoji": "😨", "label": "Fear",         "starter": "I'm consumed by fear and don't know how to face it"},
    {"emoji": "😵", "label": "Confusion",    "starter": "I feel completely confused and don't know what path to take"},
    {"emoji": "😒", "label": "Jealousy",     "starter": "I can't stop feeling jealous and it's eating me up inside"},
    {"emoji": "😔", "label": "Loneliness",   "starter": "I feel deeply lonely even when surrounded by people"},
    {"emoji": "💔", "label": "Failure",      "starter": "I feel like a failure and don't know how to move forward"},
    {"emoji": "🌀", "label": "Overthinking", "starter": "My mind won't stop — I keep overthinking everything"},
    {"emoji": "🌑", "label": "Purpose",      "starter": "I feel lost and don't know what my purpose in life is"},
]

# --- Initialize Session States ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "backend_connected" not in st.session_state:
    st.session_state.backend_connected = False
if "prefill_input" not in st.session_state:
    st.session_state.prefill_input = ""

# --- Premium Spiritual CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800&family=Noto+Sans+Devanagari:wght@400;600;700&display=swap');

    /* ── Global ───────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #080d1e;
        color: #dde0f5;
    }
    .stApp {
        background: linear-gradient(160deg, #080d1e 0%, #0d1228 50%, #0a0e20 100%);
    }

    /* ── Header ───────────────────────────────────────── */
    .gita-header {
        text-align: center;
        padding: 2.2rem 1rem 0.6rem;
    }
    .gita-om {
        font-size: 3rem;
        margin-bottom: 0.2rem;
        filter: drop-shadow(0 0 18px #FF9F2088);
        animation: pulse-glow 3s ease-in-out infinite;
    }
    @keyframes pulse-glow {
        0%, 100% { filter: drop-shadow(0 0 10px #FF9F2066); }
        50%       { filter: drop-shadow(0 0 28px #FF9F20cc); }
    }
    .gita-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF8C00 0%, #FFD700 50%, #FF6B00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
        line-height: 1.15;
        margin: 0;
    }
    .gita-subtitle {
        color: #8888b8;
        font-size: 1rem;
        font-weight: 400;
        margin-top: 0.35rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        font-size: 0.78rem;
    }
    .gita-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #FFD70044, #FF8C0066, #FFD70044, transparent);
        margin: 1.4rem auto 0.5rem;
        width: 70%;
    }

    /* ── Emotion Cards Section ────────────────────────── */
    .emotion-section-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #c8cce8;
        text-align: center;
        margin: 1.6rem 0 1rem;
        letter-spacing: 0.02em;
    }
    .emotion-section-title span {
        color: #FF9F20;
    }
    .emotion-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.65rem;
        margin: 0 0 1.4rem;
        padding: 0 0.2rem;
    }
    @media (max-width: 768px) {
        .emotion-grid { grid-template-columns: repeat(2, 1fr); }
        .gita-title   { font-size: 1.8rem; }
        .welcome-banner { padding: 1.5rem 1.2rem; }
        .ag-verse-card  { padding: 0.9rem 1rem; }
    }
    @media (max-width: 480px) {
        .emotion-grid   { grid-template-columns: repeat(2, 1fr); gap: 0.45rem; }
        .gita-title     { font-size: 1.5rem; }
        .gita-om        { font-size: 2.2rem; }
        .gita-subtitle  { font-size: 0.7rem; }
        .welcome-banner { padding: 1.2rem 0.9rem; border-radius: 12px; }
        .welcome-banner .wb-title { font-size: 1.05rem; }
        .welcome-banner .wb-text  { font-size: 0.82rem; }
        .ag-verse-card  { padding: 0.75rem 0.85rem; }
        .ag-sanskrit    { font-size: 1rem; }
        .ag-action-card { flex-direction: column; gap: 0.4rem; }
        .vod-card       { padding: 0.85rem 0.9rem; }
        .vod-sanskrit   { font-size: 0.88rem; }
    }
    .emotion-card {
        background: linear-gradient(135deg, #111633 0%, #161d3a 100%);
        border: 1px solid #2a2e5a;
        border-radius: 14px;
        padding: 0.85rem 0.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.22s ease;
        box-shadow: 0 2px 14px rgba(0,0,0,0.35);
        text-decoration: none;
        display: block;
    }
    .emotion-card:hover {
        border-color: #FF8C0077;
        background: linear-gradient(135deg, #1a1d40 0%, #201f48 100%);
        box-shadow: 0 4px 22px rgba(255, 140, 0, 0.18);
        transform: translateY(-2px);
    }
    .emotion-card .ec-emoji {
        font-size: 1.6rem;
        display: block;
        margin-bottom: 0.3rem;
    }
    .emotion-card .ec-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #c0c4e8;
        letter-spacing: 0.04em;
    }

    /* ── Structured Response Cards ────────────────────── */
    .ag-response-wrapper {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        margin-top: 0.5rem;
    }
    .ag-emotion-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: linear-gradient(135deg, #1a1040, #2a1560);
        border: 1px solid #7B2FBE55;
        border-radius: 24px;
        padding: 0.35rem 0.85rem;
        font-size: 0.85rem;
        font-weight: 600;
        color: #c084fc;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .ag-root-cause {
        background: #111228;
        border-left: 3px solid #7B2FBE;
        border-radius: 0 8px 8px 0;
        padding: 0.6rem 0.9rem;
        font-size: 0.9rem;
        color: #b0b0d0;
        font-style: italic;
    }
    .ag-verse-card {
        background: linear-gradient(135deg, #1a1430 0%, #1e1838 100%);
        border: 1px solid #FF8C0033;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        box-shadow: 0 4px 24px rgba(255, 140, 0, 0.08), inset 0 1px 0 rgba(255,255,255,0.04);
    }
    .ag-verse-ref {
        font-family: 'Outfit', sans-serif;
        font-size: 0.75rem;
        font-weight: 700;
        color: #FF8C00;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.6rem;
    }
    .ag-sanskrit {
        font-family: 'Noto Sans Devanagari', serif;
        font-size: 1.2rem;
        color: #fff;
        line-height: 1.7;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .ag-transliteration {
        font-style: italic;
        color: #9090c0;
        font-size: 0.85rem;
        text-align: center;
        margin-bottom: 0.8rem;
    }
    .ag-meaning {
        color: #d0d0ec;
        font-size: 0.92rem;
        line-height: 1.6;
        border-top: 1px solid #ffffff12;
        padding-top: 0.7rem;
    }
    .ag-fit-card {
        background: #131830;
        border: 1px solid #3355aa33;
        border-left: 3px solid #5580ff;
        border-radius: 0 10px 10px 0;
        padding: 0.8rem 1rem;
        font-size: 0.9rem;
        color: #c8cef0;
        line-height: 1.6;
    }
    .ag-fit-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #6688ff;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.35rem;
    }
    .ag-action-card {
        background: linear-gradient(135deg, #152212 0%, #1a2c14 100%);
        border: 1px solid #66bb6a44;
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
        font-size: 0.9rem;
        color: #c8e6c9;
        line-height: 1.6;
        display: flex;
        gap: 0.7rem;
        align-items: flex-start;
    }
    .ag-action-icon {
        font-size: 1.2rem;
        flex-shrink: 0;
        margin-top: 0.05rem;
    }
    .ag-action-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #81c784;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.3rem;
    }
    .ag-crisis-note {
        background: #1e1205;
        border: 1px solid #ff980044;
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
        font-size: 0.82rem;
        color: #ffcc80;
        margin-top: 0.25rem;
    }

    /* ── Sidebar ──────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #080c1c !important;
        border-right: 1px solid #181e38;
    }
    .sb-brand {
        text-align: center;
        padding: 0.6rem 0 1.2rem;
        border-bottom: 1px solid #181e38;
        margin-bottom: 0.8rem;
    }
    .sb-brand-name {
        font-family: 'Outfit', sans-serif;
        font-size: 1.15rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF8C00, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .sb-brand-sub {
        font-size: 0.68rem;
        color: #4a4a80;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-top: 0.2rem;
    }
    .sb-header {
        font-family: 'Outfit', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        color: #4a4a80;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-top: 1.4rem;
        margin-bottom: 0.6rem;
        padding-bottom: 0.3rem;
        border-bottom: 1px solid #181e38;
    }

    /* ── Verse of the Day Card ────────────────────────── */
    .vod-card {
        background: linear-gradient(135deg, #14112e, #1a1535);
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        border: 1px solid #FF8C0040;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,215,0,0.06);
        margin-bottom: 0.6rem;
    }
    .vod-ref {
        font-family: 'Outfit', sans-serif;
        color: #FF9F20;
        font-weight: 700;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .vod-ref::before {
        content: "✦";
        color: #FFD700;
    }
    .vod-sanskrit {
        font-family: 'Noto Sans Devanagari', serif;
        font-size: 0.98rem;
        color: #FFFFFF;
        line-height: 1.65;
        margin-bottom: 0.4rem;
        text-align: center;
    }
    .vod-translit {
        font-style: italic;
        color: #7a7ca8;
        font-size: 0.78rem;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .vod-translation {
        color: #b8bce0;
        font-size: 0.82rem;
        line-height: 1.55;
        border-top: 1px solid #ffffff0e;
        padding-top: 0.5rem;
    }
    .vod-theme {
        font-size: 0.68rem;
        font-weight: 700;
        color: #FF9F20;
        margin-top: 0.6rem;
        display: block;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        opacity: 0.85;
    }

    /* ── Chapter Explorer ─────────────────────────────── */
    .ch-card {
        background: linear-gradient(135deg, #0f1428 0%, #131830 100%);
        border: 1px solid #2a2e58;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-top: 0.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.3);
    }
    .ch-name {
        font-family: 'Outfit', sans-serif;
        font-size: 0.88rem;
        font-weight: 700;
        color: #e0e4ff;
        margin-bottom: 0.2rem;
    }
    .ch-meta {
        font-size: 0.72rem;
        color: #5a5a90;
        letter-spacing: 0.04em;
        margin-bottom: 0.5rem;
    }
    .ch-summary {
        font-size: 0.8rem;
        color: #9090c0;
        line-height: 1.55;
    }

    /* ── Chat Input ───────────────────────────────────── */
    [data-testid="stChatInput"] textarea {
        background: #0f1228 !important;
        border: 1px solid #252848 !important;
        color: #dde0f5 !important;
        border-radius: 14px !important;
        font-size: 0.95rem !important;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: #FF8C0077 !important;
        box-shadow: 0 0 0 2px #FF8C0022 !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #484870 !important;
    }

    /* ── Buttons ──────────────────────────────────────── */
    .stButton>button {
        background: linear-gradient(135deg, #FF8C00, #FF6F00) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 10px rgba(255,140,0,0.25) !important;
    }
    .stButton>button:hover {
        opacity: 0.88 !important;
        box-shadow: 0 4px 18px rgba(255,140,0,0.4) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Chat Messages ────────────────────────────────── */
    [data-testid="stChatMessageContent"] {
        background: transparent !important;
    }

    /* ── Welcome Banner ───────────────────────────────── */
    .welcome-banner {
        background: linear-gradient(135deg, #15112e 0%, #1c1540 100%);
        border: 1px solid #FF8C0030;
        border-radius: 18px;
        padding: 2rem 2.5rem;
        text-align: center;
        margin: 0.5rem 0 1.8rem;
        box-shadow: 0 8px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,215,0,0.06);
    }
    .welcome-banner .wb-icon { font-size: 2.5rem; margin-bottom: 0.7rem; }
    .welcome-banner .wb-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFD700;
        margin-bottom: 0.5rem;
    }
    .welcome-banner .wb-text {
        color: #8080b0;
        font-size: 0.9rem;
        line-height: 1.6;
        max-width: 520px;
        margin: 0 auto;
    }

    /* ── Scrollbar ────────────────────────────────────── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #080d1e; }
    ::-webkit-scrollbar-thumb { background: #252848; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ───────────────────────────────────────────────────────────────────────────
# Helper: Parse LLM structured response into sections
# ───────────────────────────────────────────────────────────────────────────
def parse_gita_response(text: str) -> dict:
    """
    Parses the structured Gita Counselor LLM output into a dict of sections.
    Returns a dict with keys: emotion, root_cause, verse_ref, sanskrit,
    transliteration, meaning, why_fits, practical_action, crisis_note, raw.
    """
    sections = {
        "emotion": None,
        "root_cause": None,
        "verse_ref": None,
        "sanskrit": None,
        "transliteration": None,
        "meaning": None,
        "why_fits": None,
        "practical_action": None,
        "crisis_note": None,
        "raw": text,
        "parsed": False
    }

    def extract_section(label: str, next_labels: list) -> Optional[str]:
        escaped_label = re.escape(label)
        end_pattern = "|".join(re.escape(f"**{lbl}:**") for lbl in next_labels)
        if end_pattern:
            pattern = rf"\*\*{escaped_label}:\*\*\s*(.*?)(?={end_pattern}|$)"
        else:
            pattern = rf"\*\*{escaped_label}:\*\*\s*(.*?)$"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    LABELS_ORDER = [
        "Emotion Detected",
        "Possible Root Cause",
        "Relevant Verse",
        "Sanskrit",
        "Transliteration",
        "Meaning",
        "Why This Fits",
        "Practical Action"
    ]

    sections["emotion"]          = extract_section("Emotion Detected",  LABELS_ORDER[1:])
    sections["root_cause"]       = extract_section("Possible Root Cause", LABELS_ORDER[2:])
    sections["verse_ref"]        = extract_section("Relevant Verse",    LABELS_ORDER[3:])
    sections["sanskrit"]         = extract_section("Sanskrit",          LABELS_ORDER[4:])
    sections["transliteration"]  = extract_section("Transliteration",   LABELS_ORDER[5:])
    sections["meaning"]          = extract_section("Meaning",           LABELS_ORDER[6:])
    sections["why_fits"]         = extract_section("Why This Fits",     LABELS_ORDER[7:])
    sections["practical_action"] = extract_section("Practical Action",  [])

    if "⚠️" in text or "qualified professional" in text.lower():
        crisis_match = re.search(r"(⚠️.*?)(?:\n|$)", text)
        if crisis_match:
            sections["crisis_note"] = crisis_match.group(1).strip()

    if sections["emotion"] and sections["meaning"]:
        sections["parsed"] = True

    return sections


def render_gita_response(sections: dict):
    """Renders parsed Gita Counselor response as rich HTML cards."""
    if not sections["parsed"]:
        st.markdown(sections["raw"])
        return

    html_parts = ['<div class="ag-response-wrapper">']

    if sections["emotion"]:
        html_parts.append(
            f'<div><span class="ag-emotion-badge">🌊 {sections["emotion"]}</span></div>'
        )

    if sections["root_cause"]:
        html_parts.append(
            f'<div class="ag-root-cause"><strong style="color:#9090c8;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;">Root Cause</strong><br/>{sections["root_cause"]}</div>'
        )

    verse_parts = []
    if sections["verse_ref"]:
        verse_parts.append(f'<div class="ag-verse-ref">📜 {sections["verse_ref"]}</div>')
    if sections["sanskrit"]:
        verse_parts.append(f'<div class="ag-sanskrit">{sections["sanskrit"]}</div>')
    if sections["transliteration"]:
        verse_parts.append(f'<div class="ag-transliteration">{sections["transliteration"]}</div>')
    if sections["meaning"]:
        verse_parts.append(f'<div class="ag-meaning">{sections["meaning"]}</div>')
    if verse_parts:
        html_parts.append(f'<div class="ag-verse-card">{"".join(verse_parts)}</div>')

    if sections["why_fits"]:
        html_parts.append(
            f'<div class="ag-fit-card">'
            f'<div class="ag-fit-label">💡 Why This Fits</div>'
            f'{sections["why_fits"]}'
            f'</div>'
        )

    if sections["practical_action"]:
        html_parts.append(
            f'<div class="ag-action-card">'
            f'<div class="ag-action-icon">🎯</div>'
            f'<div><div class="ag-action-label">Practical Teaching</div>{sections["practical_action"]}</div>'
            f'</div>'
        )

    if sections["crisis_note"]:
        html_parts.append(f'<div class="ag-crisis-note">{sections["crisis_note"]}</div>')

    html_parts.append('</div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)


# ───────────────────────────────────────────────────────────────────────────
# Helper: Backend connectivity
# ───────────────────────────────────────────────────────────────────────────
def ping_backend() -> bool:
    try:
        response = requests.get(f"{BACKEND_URL}/chapter_summary?chapter=1", timeout=3)
        if response.status_code == 200:
            st.session_state.backend_connected = True
            return True
    except Exception:
        pass
    st.session_state.backend_connected = False
    return False


# ───────────────────────────────────────────────────────────────────────────
# Helper: Validate Verse of the Day data integrity
# ───────────────────────────────────────────────────────────────────────────
def validate_and_render_vod(vod: dict) -> bool:
    """
    Validates that all verse fields originate from the same verse record.
    Returns True if valid, False if a mismatch is detected.

    The API now returns camelCase keys (chapterNumber, verseNumber) plus legacy
    snake_case aliases (chapter, verse) for backward compatibility.

    Validation tests:
      - Ch 4 V 7  → transliteration must contain 'yada yada hi'
      - Ch 12 V 13 → transliteration must contain 'adveshta'
    """
    ch  = vod.get("chapterNumber") or vod.get("chapter")
    v   = vod.get("verseNumber")   or vod.get("verse")
    sk  = vod.get("sanskrit", "")
    tr  = vod.get("transliteration", "").lower()
    tl  = vod.get("translation", "")

    # Basic presence check
    if not (ch and v and sk and tl):
        st.warning("⚠️ Verse data incomplete — skipping display.")
        return False

    # Cross-field integrity checks
    mismatch_detected = False
    if ch == 4 and v == 7:
        if "yada yada hi" not in tr:
            mismatch_detected = True
            print(f"[VERSE MISMATCH] Ch4V7 expected 'yada yada hi' in transliteration but got: {tr[:60]}")
    if ch == 12 and v == 13:
        if "adveshta" not in tr:
            mismatch_detected = True
            print(f"[VERSE MISMATCH] Ch12V13 expected 'adveshta' in transliteration but got: {tr[:60]}")

    if mismatch_detected:
        st.error("⚠️ Verse integrity check failed — cross-verse data mixing detected. Please refresh.")
        return False

    return True


def render_verse_of_the_day(vod: dict):
    """Renders a validated Verse of the Day card."""
    ch  = vod.get("chapterNumber") or vod.get("chapter")
    v   = vod.get("verseNumber")   or vod.get("verse")
    sk  = vod.get("sanskrit", "")
    tr  = vod.get("transliteration", "")
    tl  = vod.get("translation", "")
    th  = vod.get("theme", "")
    sm  = vod.get("summary", "")

    # Use summary as extra context if available
    practical = sm if sm else th

    st.markdown(f"""
    <div class='vod-card'>
        <div class='vod-ref'>Chapter {ch}, Verse {v}</div>
        <div class='vod-sanskrit'>{sk}</div>
        <div class='vod-translit'>{tr}</div>
        <div class='vod-translation'>"{tl}"</div>
        <span class='vod-theme'>✦ {practical}</span>
    </div>
    """, unsafe_allow_html=True)


# Perform connection check on start
ping_backend()


# ───────────────────────────────────────────────────────────────────────────
# Page Header
# ───────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="gita-header">
    <div class="gita-om">🕉️</div>
    <div class="gita-title">Bhagavad Gita AI Counselor</div>
    <div class="gita-subtitle">Wisdom for Modern Life</div>
</div>
<hr class="gita-divider"/>
""", unsafe_allow_html=True)

# Connection alert
if not st.session_state.backend_connected:
    st.error("⚠️ Unable to connect to the backend. Please start the FastAPI server.")
    st.code("python -m uvicorn api.main:app --reload", language="bash")
    st.stop()


# ───────────────────────────────────────────────────────────────────────────
# Sidebar
# ───────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Branding
    st.markdown("""
    <div class='sb-brand'>
        <div class='sb-brand-name'>🕉️ Bhagavad Gita</div>
        <div class='sb-brand-sub'>AI Counselor · Wisdom for Modern Life</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Today's Divine Guidance (Verse of the Day) ──
    st.markdown("<div class='sb-header'>🌟 Today's Divine Guidance</div>", unsafe_allow_html=True)
    try:
        vod_res = requests.get(f"{BACKEND_URL}/verse_of_the_day", timeout=5)
        if vod_res.status_code == 200:
            vod = vod_res.json()
            if validate_and_render_vod(vod):
                render_verse_of_the_day(vod)
        else:
            st.caption("Could not load today's divine guidance")
    except Exception as e:
        st.caption("Could not reach backend for today's verse")

    # ── Chapter Explorer ──
    st.markdown("<div class='sb-header'>📖 Chapter Explorer</div>", unsafe_allow_html=True)
    chapter_num = st.selectbox(
        "Select a Chapter",
        options=list(range(1, 19)),
        index=0,
        label_visibility="collapsed"
    )
    try:
        ch_res = requests.get(f"{BACKEND_URL}/chapter_summary?chapter={chapter_num}", timeout=4)
        if ch_res.status_code == 200:
            ch_data = ch_res.json()
            ch_name = ch_data.get('name_translation', '')
            ch_orig = ch_data.get('name', '')
            ch_cnt  = ch_data.get('verses_count', '')
            ch_summary = ch_data.get('summary', '')
            st.markdown(f"""
            <div class='ch-card'>
                <div class='ch-name'>Chapter {chapter_num}: {ch_name}</div>
                <div class='ch-meta'>{ch_orig} · {ch_cnt} verses</div>
                <div class='ch-summary'>{ch_summary[:220]}{'...' if len(ch_summary or '') > 220 else ''}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Failed to load chapter summary.")
    except Exception as e:
        st.error(f"Error: {e}")

    # ── Verse Search ──
    st.markdown("<div class='sb-header'>🔍 Search Verses</div>", unsafe_allow_html=True)
    search_query = st.text_input(
        "Search by keyword",
        placeholder="e.g. karma, attachment, fear...",
        label_visibility="collapsed"
    )
    if search_query:
        try:
            search_res = requests.get(f"{BACKEND_URL}/search_verse?query={search_query}", timeout=4)
            if search_res.status_code == 200:
                s_data = search_res.json()
                st.caption(f"Found {s_data.get('count')} matching verses")
                for result in s_data.get("results", []):
                    title = f"Gita {result.get('chapter')}.{result.get('verse')} — {result.get('title', '')}"
                    with st.expander(title):
                        st.markdown(f"**Sanskrit:**\n`{result.get('sanskrit')}`")
                        st.markdown(f"**Transliteration:**\n*{result.get('transliteration')}*")
                        if result.get('word_meanings'):
                            st.markdown(f"**Word Meanings:**\n{result.get('word_meanings')}")
        except Exception as e:
            st.error(f"Search error: {e}")

    # ── Clear Conversation ──
    st.markdown("<div class='sb-header'>🔄 Conversation</div>", unsafe_allow_html=True)
    if st.button("Clear Conversation", use_container_width=True, type="primary"):
        try:
            clear_res = requests.post(f"{BACKEND_URL}/clear_chat?session_id={st.session_state.session_id}")
            if clear_res.status_code == 200:
                st.session_state.messages = []
                st.success("Conversation cleared.")
                st.rerun()
            else:
                st.error("Failed to clear on server.")
        except Exception as e:
            st.error(f"Error: {e}")


# ───────────────────────────────────────────────────────────────────────────
# Main Content Area
# ───────────────────────────────────────────────────────────────────────────

# Welcome banner — always shown before any conversation starts
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-banner">
        <div class="wb-icon">🙏</div>
        <div class="wb-title">Your Spiritual Counselor Awaits</div>
        <div class="wb-text">
            The Bhagavad Gita offers timeless wisdom for every struggle life brings.
            Share what's on your heart and receive guidance rooted in ancient Vedic teaching.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Emotion Cards ──
st.markdown("""
<div class="emotion-section-title">
    How Are You Feeling Today?
    <br/><span style="font-size:0.8rem;font-weight:400;color:#5a5a90;letter-spacing:0.04em;">
    Choose an emotion or describe your situation below
    </span>
</div>
""", unsafe_allow_html=True)

# Render emotion cards in a 4-column grid using Streamlit columns
cols = st.columns(4)
for idx, card in enumerate(EMOTION_CARDS):
    with cols[idx % 4]:
        if st.button(
            f"{card['emoji']}\n{card['label']}",
            key=f"ec_{card['label']}",
            use_container_width=True,
            help=card["starter"]
        ):
            st.session_state.prefill_input = card["starter"]

# ── Conversation History ──
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and "sections" in msg:
            render_gita_response(msg["sections"])
        else:
            st.markdown(msg["content"])

        if "citations" in msg and msg["citations"]:
            with st.expander("📚 Gita Verses Referenced"):
                for idx, cite in enumerate(msg["citations"]):
                    st.markdown(f"**{cite.get('source', f'Verse {idx+1}')}**")
                    if cite.get("transliteration"):
                        st.caption(f"*{cite.get('transliteration')}*")
                    if cite.get("translation"):
                        st.markdown(f"> {cite.get('translation')}")
                    if idx < len(msg["citations"]) - 1:
                        st.divider()

# ── Chat Input ──
default_val = st.session_state.prefill_input
if default_val:
    st.session_state.prefill_input = ""

placeholder = default_val if default_val else "Share your thoughts, worries, questions, or struggles..."

if user_question := st.chat_input(
    placeholder,
    disabled=not st.session_state.backend_connected
):
    if True:
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Seeking wisdom from the Gita for you..."):
                try:
                    payload = {
                        "question": user_question,
                        "session_id": st.session_state.session_id
                    }
                    chat_res = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=60)

                    if chat_res.status_code == 200:
                        data = chat_res.json()
                        answer = data.get("answer", "")
                        citations = data.get("citations", [])

                        sections = parse_gita_response(answer)
                        render_gita_response(sections)

                        if citations:
                            with st.expander("📚 Gita Verses Referenced"):
                                for idx, cite in enumerate(citations):
                                    st.markdown(f"**{cite.get('source', f'Verse {idx+1}')}**")
                                    if cite.get("transliteration"):
                                        st.caption(f"*{cite.get('transliteration')}*")
                                    if cite.get("translation"):
                                        st.markdown(f"> {cite.get('translation')}")
                                    if idx < len(citations) - 1:
                                        st.divider()

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sections": sections,
                            "citations": citations
                        })

                    else:
                        detail = chat_res.json().get("detail", "Unknown error")
                        st.error(f"Error: {detail}")

                except requests.exceptions.Timeout:
                    st.error("The request timed out. The counselor may be initializing its wisdom base for the first time (this can take a few minutes). Please try again.")
                except Exception as e:
                    st.error(f"Connection error: {e}")
