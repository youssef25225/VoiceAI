import io
import time
import base64
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from html import escape

import streamlit as st
import requests

API_URL         = "https://90b6-34-50-181-193.ngrok-free.app"
MAX_HISTORY     = 20
REQUEST_TIMEOUT = 120
LANG            = "ar"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

:root {
    --bg-primary:    #f8f9fc;
    --bg-secondary:  #ffffff;
    --bg-tertiary:   #f0f2f7;
    --border:        #dde1eb;
    --border-subtle: #eef0f5;
    --accent:        #1a56db;
    --accent-dim:    #1447c0;
    --text-primary:  #111827;
    --text-secondary:#6b7280;
    --text-muted:    #9ca3af;
    --success:       #059669;
    --user-bubble:   #eff6ff;
    --shadow:        0 4px 24px rgba(0,0,0,0.06);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stApp"] {
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}

.sidebar-brand {
    font-size: 1.1rem; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--accent) !important;
    padding: 1.5rem 0 0.5rem;
}
.sidebar-divider { height: 1px; background: var(--border); margin: 1rem 0; }

.status-badge {
    display: inline-flex; align-items: center; gap: 0.5rem;
    font-size: 0.75rem; font-weight: 500; letter-spacing: 0.08em;
    text-transform: uppercase; padding: 0.4rem 0.8rem;
    border-radius: 4px; background: rgba(5,150,105,0.08);
    color: var(--success) !important; border: 1px solid rgba(5,150,105,0.2);
}
.status-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--success); animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

[data-testid="stButton"] button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important; font-weight: 500 !important;
    letter-spacing: 0.06em !important; border-radius: 6px !important;
    padding: 0.5rem 1rem !important; transition: all 0.15s ease !important;
    width: 100% !important;
}
[data-testid="stButton"] button:hover {
    border-color: var(--accent) !important; color: var(--accent) !important;
    background: rgba(26,86,219,0.04) !important;
}
[data-testid="stButton"] button[kind="primary"] {
    background: var(--accent) !important; border-color: var(--accent) !important;
    color: #fff !important; font-weight: 600 !important;
}

.page-header {
    padding: 2.5rem 0 2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.page-title { font-size: 1.6rem; font-weight: 300; color: var(--text-primary); }
.page-title span { color: var(--accent); font-weight: 600; }
.page-subtitle {
    font-size: 0.78rem; letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--text-muted); margin-top: 0.3rem; font-family: 'DM Mono', monospace;
}

.msg-row {
    display: flex; padding: 1.2rem 0;
    border-bottom: 1px solid var(--border-subtle);
    animation: fadeIn 0.2s ease;
}
@keyframes fadeIn { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:translateY(0)} }
.msg-row.user { flex-direction: row-reverse; }

.msg-avatar {
    width: 32px; height: 32px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.65rem; font-weight: 600; letter-spacing: 0.05em;
    text-transform: uppercase; flex-shrink: 0;
    font-family: 'DM Mono', monospace;
    align-self: flex-start; margin-top: 4px;
}
.msg-avatar.user-av {
    background: rgba(26,86,219,0.1); color: var(--accent);
    border: 1px solid rgba(26,86,219,0.2); margin-left: 1rem;
}
.msg-avatar.bot-av {
    background: var(--bg-tertiary); color: var(--text-muted);
    border: 1px solid var(--border); margin-right: 1rem;
}

.msg-content { flex: 1; max-width: 75%; }
.msg-row.user .msg-content { text-align: right; }

.msg-text {
    font-size: 0.9rem; line-height: 1.7; color: var(--text-primary);
    padding: 0.8rem 1rem; border-radius: 8px;
    display: inline-block; max-width: 100%; text-align: left;
    white-space: pre-wrap; word-break: break-word;
}
.msg-row.user .msg-text {
    background: var(--user-bubble);
    border: 1px solid rgba(26,86,219,0.15);
    color: var(--accent-dim);
}
.msg-row.bot .msg-text { background: transparent; border: none; padding-left: 0; }

audio { margin-top: 0.5rem; height: 32px; border-radius: 6px; width: 100%; max-width: 300px; display: block; }

[data-testid="stChatInput"] {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important; box-shadow: var(--shadow) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important; color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.875rem !important;
}

label, [data-testid="stWidgetLabel"] {
    color: var(--text-secondary) !important; font-size: 0.75rem !important;
    font-weight: 500 !important; letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

.section-label {
    font-size: 0.7rem; letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--text-muted); font-family: 'DM Mono', monospace;
    margin-bottom: 0.75rem; margin-top: 1.25rem;
}
.empty-state { text-align: center; padding: 4rem 2rem; color: var(--text-muted); }
.empty-state-title { font-size: 1rem; font-weight: 500; color: var(--text-secondary); margin-bottom: 0.5rem; }
.empty-state-sub { font-size: 0.8rem; letter-spacing: 0.06em; }
.msg-content .stMarkdown { margin: 0 !important; }
</style>
"""


@dataclass
class ChatMessage:
    role: str
    content: str
    audio: Optional[bytes] = None
    timestamp: float = field(default_factory=time.time)
    error: bool = False

    def to_api_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class VoiceAIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session  = requests.Session()
        self.session.headers.update({"Accept": "application/json", "ngrok-skip-browser-warning": "true"})

    def chat(self, history: List[Dict], user_name: str = None) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
        try:
            payload = {"history": history}
            if user_name:
                payload["user_name"] = user_name

            r = self.session.post(
                f"{self.base_url}/text",  # ← /chat بدل /text
                json={"history": history, "lang": "ar", "user_id": "guest"},
                timeout=REQUEST_TIMEOUT,
            )
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                return None, None, data["error"]
            audio_hex = data.get("audio")
            audio = bytes.fromhex(audio_hex) if audio_hex else None
            text  = data.get("reply") or data.get("text") or data.get("response")
            return audio, text, None
        except requests.exceptions.Timeout:
            return None, None, "Request timed out."
        except requests.exceptions.ConnectionError:
            return None, None, "Cannot connect to server."
        except Exception as e:
            return None, None, str(e)


def init_state():
    defaults = {
        "chat_history": [],
        "user_name": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def add_msg(msg: ChatMessage):
    st.session_state.chat_history.append(msg)
    if len(st.session_state.chat_history) > MAX_HISTORY * 2:
        st.session_state.chat_history = st.session_state.chat_history[-MAX_HISTORY * 2:]


def render_message(msg: ChatMessage, is_last: bool):
    is_user      = msg.role == "user"
    initials     = "أنت" if is_user else "AI"
    av_cls       = "user-av" if is_user else "bot-av"
    row_cls      = "user" if is_user else "bot"
    safe_content = escape(msg.content)

    audio_html = ""
    if msg.audio and not is_user:
        audio_b64 = base64.b64encode(msg.audio).decode()
        autoplay  = "autoplay" if is_last else ""
        audio_html = (
            f'<audio {autoplay} controls>'
            f'<source src="data:audio/wav;base64,{audio_b64}" type="audio/wav">'
            f'</audio>'
        )

    st.markdown(
        f'<div class="msg-row {row_cls}">'
        f'<div class="msg-avatar {av_cls}">{initials}</div>'
        f'<div class="msg-content">'
        f'<div class="msg-text">{safe_content}</div>'
        f'{audio_html}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Main ──────────────────────────────────────────────────────────────────
st.set_page_config(page_title="VoiceAI", layout="wide", initial_sidebar_state="expanded")
init_state()
client = VoiceAIClient(API_URL)
st.markdown(CSS, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">VoiceAI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="status-badge"><span class="status-dot"></span>Session Active</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # اسم اليوزر (اختياري — بيتبعت للـ LLM عشان سامح يناديه بالاسم)
    user_name_input = st.text_input("اسمك (اختياري)", value=st.session_state.user_name or "")
    if user_name_input.strip():
        st.session_state.user_name = user_name_input.strip()

    st.markdown("<br>", unsafe_allow_html=True)

    msg_count = len(st.session_state.chat_history)
    st.markdown(
        f'<div style="font-size:0.75rem;color:var(--text-muted);font-family:\'DM Mono\',monospace">'
        f'{msg_count} messages</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Clear History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# ── Chat ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="page-title">Voice <span>AI</span></div>
    <div class="page-subtitle">Talk with Dr Sameh Al-Ansary</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.chat_history:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-title">جاهز للكلام</div>
        <div class="empty-state-sub">اكتب رسالتك وابدأ</div>
    </div>
    """, unsafe_allow_html=True)
else:
    n = len(st.session_state.chat_history)
    for i, msg in enumerate(st.session_state.chat_history):
        render_message(msg, is_last=(i == n - 1))

prompt = st.chat_input("اكتب رسالتك...")
if prompt and prompt.strip():
    add_msg(ChatMessage(role="user", content=prompt.strip()))
    history = [m.to_api_dict() for m in st.session_state.chat_history[-MAX_HISTORY:]]
    with st.spinner(""):
        audio_bytes, text_reply, error = client.chat(
            history,
            user_name=st.session_state.user_name,
        )
    if error:
        add_msg(ChatMessage(role="assistant", content=error, error=True))
    elif audio_bytes or text_reply:
        add_msg(ChatMessage(
            role="assistant",
            content=text_reply or "*(voice response)*",
            audio=audio_bytes,
        ))
    else:
        add_msg(ChatMessage(role="assistant", content="No response received.", error=True))
    st.rerun()
