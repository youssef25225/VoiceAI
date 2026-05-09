import base64
import time
from dataclasses import dataclass, field
from html import escape
from typing import Dict, List, Optional, Tuple

import requests
import streamlit as st

API_URL = "https://yousefemam-voiceai.hf.space"
MAX_HISTORY = 20
REQUEST_TIMEOUT = 120

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:           #0d0f14;
    --bg-card:      #13161e;
    --bg-input:     #1a1e2a;
    --border:       rgba(255,255,255,0.07);
    --border-glow:  rgba(99,179,237,0.25);
    --accent:       #63b3ed;
    --accent-dim:   #4a9dd4;
    --accent-glow:  rgba(99,179,237,0.15);
    --text:         #e8eaf0;
    --text-sub:     #8892a4;
    --text-muted:   #4a5568;
    --user-bg:      rgba(99,179,237,0.08);
    --success:      #68d391;
    --danger:       #fc8181;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stApp"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Sora', sans-serif !important;
}

[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text) !important;
    font-family: 'Sora', sans-serif !important;
}

.brand {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 1.8rem 0 1rem;
}
.brand-icon {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, var(--accent), #a78bfa);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem;
}
.brand-name {
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    background: linear-gradient(90deg, var(--accent), #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.divider { height: 1px; background: var(--border); margin: 1rem 0; }

.badge {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0.4rem 0.75rem;
    border-radius: 20px;
    background: rgba(104,211,145,0.08);
    color: var(--success) !important;
    border: 1px solid rgba(104,211,145,0.2);
    font-family: 'JetBrains Mono', monospace;
}
.badge-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--success);
    animation: blink 2.2s ease infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

.stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0;
}
.stat-label {
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-muted);
    font-family: 'JetBrains Mono', monospace;
}
.stat-value {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--accent);
    font-family: 'JetBrains Mono', monospace;
}

[data-testid="stButton"] button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-sub) !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    border-radius: 8px !important;
    padding: 0.55rem 1rem !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
[data-testid="stButton"] button:hover {
    border-color: var(--danger) !important;
    color: var(--danger) !important;
    background: rgba(252,129,129,0.05) !important;
}

[data-testid="stTextInput"] input {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.85rem !important;
    padding: 0.6rem 0.9rem !important;
    transition: border-color 0.2s ease !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--border-glow) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
    outline: none !important;
}

label, [data-testid="stWidgetLabel"] p {
    color: var(--text-muted) !important;
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.page-header {
    padding: 2.8rem 0 2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2.5rem;
    position: relative;
}
.page-header::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0;
    width: 80px; height: 1px;
    background: linear-gradient(90deg, var(--accent), transparent);
}
.page-title {
    font-size: 1.9rem;
    font-weight: 300;
    color: var(--text);
    line-height: 1.2;
}
.page-title strong {
    font-weight: 700;
    background: linear-gradient(90deg, var(--accent), #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.page-subtitle {
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-top: 0.4rem;
    font-family: 'JetBrains Mono', monospace;
}

.msg-wrap {
    display: flex;
    padding: 1rem 0;
    border-bottom: 1px solid var(--border);
    animation: rise 0.25s ease;
}
@keyframes rise { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
.msg-wrap.user { flex-direction: row-reverse; }

.avatar {
    width: 34px; height: 34px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.6rem; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase;
    flex-shrink: 0;
    font-family: 'JetBrains Mono', monospace;
    align-self: flex-start;
    margin-top: 2px;
}
.avatar.user-av {
    background: var(--user-bg);
    color: var(--accent);
    border: 1px solid var(--border-glow);
    margin-left: 0.9rem;
}
.avatar.bot-av {
    background: linear-gradient(135deg, rgba(99,179,237,0.15), rgba(167,139,250,0.15));
    color: var(--accent);
    border: 1px solid var(--border);
    margin-right: 0.9rem;
}

.msg-body { flex: 1; max-width: 72%; }
.msg-wrap.user .msg-body { text-align: right; }

.bubble {
    font-size: 0.875rem;
    line-height: 1.75;
    color: var(--text);
    padding: 0.75rem 1rem;
    border-radius: 10px;
    display: inline-block;
    max-width: 100%;
    text-align: left;
    white-space: pre-wrap;
    word-break: break-word;
}
.msg-wrap.user .bubble {
    background: var(--user-bg);
    border: 1px solid var(--border-glow);
    color: var(--accent);
}
.msg-wrap.bot .bubble {
    background: transparent;
    border: none;
    padding-left: 0;
    color: var(--text);
}
.msg-wrap.bot.error .bubble { color: var(--danger); }

.meta {
    font-size: 0.63rem;
    color: var(--text-muted);
    font-family: 'JetBrains Mono', monospace;
    margin-top: 0.35rem;
    letter-spacing: 0.06em;
}

audio {
    margin-top: 0.6rem;
    height: 30px;
    border-radius: 6px;
    width: 100%;
    max-width: 280px;
    display: block;
    filter: invert(1) hue-rotate(200deg) brightness(0.85);
}

[data-testid="stChatInput"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    box-shadow: 0 0 0 1px rgba(99,179,237,0.05), 0 8px 30px rgba(0,0,0,0.3) !important;
    transition: border-color 0.2s ease !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--border-glow) !important;
    box-shadow: 0 0 0 3px var(--accent-glow), 0 8px 30px rgba(0,0,0,0.3) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--text) !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.875rem !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--text-muted) !important; }

[data-testid="stSpinner"] { color: var(--accent) !important; }

.empty-state {
    text-align: center;
    padding: 5rem 2rem;
}
.empty-icon {
    font-size: 2.5rem;
    margin-bottom: 1.2rem;
    opacity: 0.4;
}
.empty-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-sub);
    margin-bottom: 0.4rem;
}
.empty-sub {
    font-size: 0.75rem;
    color: var(--text-muted);
    letter-spacing: 0.08em;
    font-family: 'JetBrains Mono', monospace;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
</style>
"""


@dataclass
class ChatMessage:
    role: str
    content: str
    audio: Optional[bytes] = None
    timestamp: float = field(default_factory=time.time)
    error: bool = False
    # ✅ FIX 1: cache base64 so we don't re-encode on every render
    _audio_b64: Optional[str] = field(default=None, repr=False)

    def to_api_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}

    @property
    def audio_b64(self) -> str:
        if self._audio_b64 is None and self.audio:
            self._audio_b64 = base64.b64encode(self.audio).decode()
        return self._audio_b64 or ""


# ✅ FIX 2: cache the client — built once per session, not on every rerun
@st.cache_resource
def get_client() -> "VoiceAIClient":
    return VoiceAIClient(API_URL)


# ✅ FIX 3: cache CSS — sent once, not on every rerun
@st.cache_data
def get_css() -> str:
    return CSS


class VoiceAIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "ngrok-skip-browser-warning": "true",
        })

    def chat(
        self,
        history: List[Dict],
        user_name: Optional[str] = None,
    ) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
        try:
            payload = {"history": history, "lang": "ar", "user_id": "guest"}
            if user_name:
                payload["user_name"] = user_name

            r = self.session.post(
                f"{self.base_url}/text",
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            r.raise_for_status()

            if not r.content:
                return None, None, "Server returned an empty response."

            content_type = r.headers.get("Content-Type", "")

            if "audio/wav" in content_type or r.content[:4] == b"RIFF":
                reply_text = (
                    r.headers.get("X-Reply")
                    or r.headers.get("X-Text")
                    or r.headers.get("X-Response")
                    or ""
                )
                return r.content, reply_text, None

            if "application/json" in content_type:
                data = r.json()
                if "error" in data:
                    return None, None, data["error"]
                audio_hex = data.get("audio")
                audio = bytes.fromhex(audio_hex) if audio_hex else None
                text = data.get("reply") or data.get("text") or data.get("response")
                return audio, text, None

            return None, None, f"Unhandled content type: {content_type}"

        except requests.exceptions.JSONDecodeError as e:
            return None, None, f"Invalid JSON: {e}"
        except requests.exceptions.Timeout:
            return None, None, "Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            return None, None, "Cannot connect to server. Check your connection."
        except requests.exceptions.HTTPError:
            return None, None, f"HTTP {r.status_code}: {r.text[:200]}"
        except Exception as e:
            return None, None, str(e)


def init_state():
    defaults = {"chat_history": [], "user_name": None}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def add_message(msg: ChatMessage):
    st.session_state.chat_history.append(msg)
    cap = MAX_HISTORY * 2
    if len(st.session_state.chat_history) > cap:
        st.session_state.chat_history = st.session_state.chat_history[-cap:]


def format_time(ts: float) -> str:
    return time.strftime("%H:%M", time.localtime(ts))


# ✅ FIX 4: build all messages as one HTML string → single st.markdown call
#    instead of one call per message (was O(n) markdown calls → now O(1))
def render_all_messages(messages: List[ChatMessage]) -> str:
    if not messages:
        return ""

    parts: List[str] = []
    total = len(messages)

    for i, msg in enumerate(messages):
        is_user = msg.role == "user"
        is_last = i == total - 1
        initials = "أنت" if is_user else "AI"
        av_cls = "user-av" if is_user else "bot-av"
        row_cls = "user" if is_user else f"bot{'  error' if msg.error else ''}"
        safe_text = escape(msg.content)
        ts = format_time(msg.timestamp)

        audio_html = ""
        if msg.audio and not is_user:
            auto = "autoplay" if is_last else ""
            audio_html = (
                f'<audio {auto} controls>'
                f'<source src="data:audio/wav;base64,{msg.audio_b64}" type="audio/wav">'
                f'</audio>'
            )

        parts.append(
            f'<div class="msg-wrap {row_cls}">'
            f'  <div class="avatar {av_cls}">{initials}</div>'
            f'  <div class="msg-body">'
            f'    <div class="bubble">{safe_text}</div>'
            f'    {audio_html}'
            f'    <div class="meta">{ts}</div>'
            f'  </div>'
            f'</div>'
        )

    return "".join(parts)


# ── App bootstrap ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="VoiceAI", layout="wide", initial_sidebar_state="expanded")
init_state()
st.markdown(get_css(), unsafe_allow_html=True)   # cached

client = get_client()                             # cached (single session)

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        '<div class="brand">'
        '<div class="brand-icon">🎙</div>'
        '<div class="brand-name">VoiceAI</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="badge"><span class="badge-dot"></span>Session Active</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    msg_count = len(st.session_state.chat_history)
    user_count = sum(1 for m in st.session_state.chat_history if m.role == "user")

    st.markdown(
        f'<div class="stat-row">'
        f'  <span class="stat-label">Messages</span>'
        f'  <span class="stat-value">{msg_count}</span>'
        f'</div>'
        f'<div class="stat-row">'
        f'  <span class="stat-label">Turns</span>'
        f'  <span class="stat-value">{user_count}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🗑 Clear Conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# ── Main area ──────────────────────────────────────────────────────────────────

st.markdown(
    '<div class="page-header">'
    '  <div class="page-title">Talk with <strong>الدحيح</strong></div>'
    '</div>',
    unsafe_allow_html=True,
)

# ✅ FIX 5: one container — messages rendered as single HTML block
chat_area = st.container()

with chat_area:
    if not st.session_state.chat_history:
        st.markdown(
            '<div class="empty-state">'
            '  <div class="empty-icon">🎙️</div>'
            '  <div class="empty-title">جاهز للكلام</div>'
            '  <div class="empty-sub">اكتب رسالتك وابدأ المحادثة</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        # single markdown call for ALL messages
        st.markdown(render_all_messages(st.session_state.chat_history), unsafe_allow_html=True)

# ── Input ──────────────────────────────────────────────────────────────────────

prompt = st.chat_input("اكتب رسالتك...")
if prompt and prompt.strip():
    add_message(ChatMessage(role="user", content=prompt.strip()))

    history = [m.to_api_dict() for m in st.session_state.chat_history[-MAX_HISTORY:]]

    with st.spinner(""):
        audio_bytes, text_reply, error = client.chat(
            history,
            user_name=st.session_state.user_name,
        )

    if error:
        add_message(ChatMessage(role="assistant", content=f"⚠ {error}", error=True))
    elif audio_bytes or text_reply:
        display_text = text_reply.strip() if text_reply and text_reply.strip() else ""
        add_message(ChatMessage(
            role="assistant",
            content=display_text,
            audio=audio_bytes,
        ))
    else:
        add_message(ChatMessage(role="assistant", content="⚠ No response received.", error=True))

    st.rerun()
