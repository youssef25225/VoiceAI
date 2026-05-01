import io
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from enum import Enum, auto

import streamlit as st
import requests

# ─────────────────────────────────────────
API_URL = "https://yousefemam-voiceai.hf.space"
MAX_HISTORY = 20
REQUEST_TIMEOUT = 120
SUPPORTED_LANGS = {"ar": "Arabic", "en": "English", "fr": "French"}


# ─────────────────────────────────────────
class AppState(Enum):
    UNKNOWN_USER = auto()   # voice not recognised → show enrollment UI
    CHATTING     = auto()   # known user, normal chat flow


@dataclass
class ChatMessage:
    role: str
    content: str
    audio: Optional[bytes] = None
    timestamp: float = field(default_factory=time.time)
    error: bool = False

    def to_api_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


# ─────────────────────────────────────────
class VoiceAIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def health_check(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/health", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def identify_voice(self, audio_bytes: bytes) -> Tuple[Optional[str], Optional[str]]:
        """POST /identify → {"user_id": "..."} | Returns (user_id, error)."""
        try:
            files = {"file": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")}
            r = self.session.post(f"{self.base_url}/identify", files=files, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                return None, data["error"]
            return data.get("user_id"), None
        except requests.exceptions.Timeout:
            return None, "Request timed out."
        except requests.exceptions.ConnectionError:
            return None, "Cannot connect to server."
        except Exception as e:
            return None, str(e)

    def enroll_voice(self, audio_bytes: bytes, user_id: str, name: str) -> Optional[str]:
        """POST /enroll → {"status": "ok"} | Returns error string or None."""
        try:
            files = {"file": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")}
            r = self.session.post(
                f"{self.base_url}/enroll",
                files=files,
                data={"user_id": user_id, "name": name},
                timeout=REQUEST_TIMEOUT,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("error")
        except Exception as e:
            return str(e)

    def chat_with_voice(
        self, audio_bytes: bytes, history: List[Dict], lang: str, user_id: str
    ) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
        """POST /voice → {"reply": "...", "audio": "<hex>"} | Returns (audio_bytes, text, error)."""
        try:
            files = {"file": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")}
            r = self.session.post(
                f"{self.base_url}/voice",
                files=files,
                data={"user_id": user_id, "lang": lang},
                timeout=REQUEST_TIMEOUT,
            )
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                return None, None, data["error"]
            audio_hex = data.get("audio")
            audio = bytes.fromhex(audio_hex) if audio_hex else None
            text = data.get("reply") or data.get("text")
            return audio, text, None
        except requests.exceptions.Timeout:
            return None, None, "Request timed out."
        except requests.exceptions.ConnectionError:
            return None, None, "Cannot connect to server."
        except Exception as e:
            return None, None, str(e)


# ─────────────────────────────────────────
class SessionState:
    @staticmethod
    def init():
        defaults = {
            "chat_history": [],
            "app_state": AppState.CHATTING,
            "identified_user_id": None,
            "identified_name": None,
            "lang": "ar",
            "api_status": False,
            "last_health_check": 0,
            "audio_key": 0,
            "enroll_key": 0,
            "pending_audio": None,
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    @staticmethod
    def add_message(msg: ChatMessage):
        st.session_state.chat_history.append(msg)
        if len(st.session_state.chat_history) > MAX_HISTORY * 2:
            st.session_state.chat_history = st.session_state.chat_history[-MAX_HISTORY * 2:]

    @staticmethod
    def clear_chat():
        st.session_state.chat_history = []

    @staticmethod
    def reset_identity():
        st.session_state.identified_user_id = None
        st.session_state.identified_name = None
        st.session_state.app_state = AppState.CHATTING
        st.session_state.pending_audio = None


# ─────────────────────────────────────────
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Space+Grotesk:wght@300;400;600;700&display=swap');

html, body, .stApp { background: #080a0f !important; font-family: 'Space Grotesk', sans-serif; }

section[data-testid="stSidebar"] {
    background: #0d0f16 !important;
    border-right: 1px solid #161a28;
}

.topbar {
    display: flex; justify-content: space-between; align-items: center;
    padding: 1.1rem 0 1.3rem; border-bottom: 1px solid #161a28; margin-bottom: 1.2rem;
}
.topbar-title { font-size: 1.3rem; font-weight: 700; color: #dde1f0; letter-spacing: -0.03em; }
.topbar-sub { font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: #404460; margin-top: 2px; }
.pill {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
    padding: 4px 12px; border-radius: 100px;
    background: #0d0f16; border: 1px solid #1e2235; color: #5a6080;
}
.pill.online { color: #4ade80; border-color: #14532d; background: #071409; }
.pill.known  { color: #60a5fa; border-color: #1e3a5f; background: #070d1a; }

div[data-testid="stChatMessage"] > div:last-child {
    background: #0e1018 !important; border: 1px solid #161a28 !important;
    border-radius: 10px !important; padding: 10px 15px !important;
    color: #c2c6dc !important; font-size: 0.88rem !important;
}

.banner {
    border-radius: 10px; padding: 14px 18px; margin-bottom: 1rem;
    font-size: 0.85rem; border: 1px solid;
}
.banner.warn    { background: #1a1200; border-color: #3d2e00; color: #d4a017; }
.banner.info    { background: #0a0f1a; border-color: #1e3050; color: #60a5fa; }
.banner.success { background: #071409; border-color: #14532d; color: #4ade80; }

.empty { text-align: center; padding: 4rem 1rem; color: #303450; }
.empty h3 { font-size: 1rem; color: #404565; margin-bottom: .4rem; }
.empty p { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; }

.stButton > button {
    background: #0e1018 !important; border: 1px solid #1e2235 !important;
    color: #7a80a0 !important; border-radius: 8px !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.78rem !important;
    transition: all .15s !important;
}
.stButton > button:hover {
    border-color: #3a4060 !important; color: #c2c6dc !important; background: #14172a !important;
}
button[kind="primary"] {
    background: #1a3a6a !important; border-color: #2a5aaa !important; color: #90c0ff !important;
}

.stTextInput input, div[data-baseweb="select"] * {
    background: #0e1018 !important; border-color: #1e2235 !important;
    color: #c2c6dc !important; font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important; border-radius: 8px !important;
}
.stDivider { border-color: #161a28 !important; }
small, .stCaption { color: #404460 !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 0.7rem !important; }
</style>
"""


# ─────────────────────────────────────────
def render_topbar(client: VoiceAIClient):
    now = time.time()
    if now - st.session_state.last_health_check > 60:
        st.session_state.api_status = client.health_check()
        st.session_state.last_health_check = now

    api_cls  = "online" if st.session_state.api_status else ""
    api_txt  = "● api online" if st.session_state.api_status else "● api offline"
    user_txt = st.session_state.identified_name or "unknown"
    user_cls = "known" if st.session_state.identified_name else ""

    st.markdown(f"""
    <div class="topbar">
        <div>
            <div class="topbar-title">🎤 VoiceAI</div>
            <div class="topbar-sub">voice-in · text + audio-out</div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;">
            <span class="pill {user_cls}">👤 {user_txt}</span>
            <span class="pill {api_cls}">{api_txt}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.divider()

        lang_options = list(SUPPORTED_LANGS.keys())
        lang_labels  = list(SUPPORTED_LANGS.values())
        idx = lang_options.index(st.session_state.lang) if st.session_state.lang in lang_options else 0
        selected = st.selectbox("Language / اللغة", lang_labels, index=idx)
        new_lang = lang_options[lang_labels.index(selected)]
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()

        st.divider()
        st.caption(f"Messages: {len(st.session_state.chat_history)}")
        if st.session_state.identified_name:
            st.caption(f"User: {st.session_state.identified_name}")
            st.caption(f"ID:   {st.session_state.identified_user_id}")

        st.divider()
        if st.button("🔄 Switch User", use_container_width=True):
            SessionState.reset_identity()
            st.session_state.audio_key += 1
            st.rerun()

        if st.button("🗑 Clear Chat", use_container_width=True):
            SessionState.clear_chat()
            st.rerun()


def render_chat_history():
    if not st.session_state.chat_history:
        st.markdown("""
        <div class="empty">
            <h3>No messages yet</h3>
            <p>Record your voice to start chatting.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    for msg in st.session_state.chat_history:
        with st.chat_message(msg.role):
            st.markdown(msg.content)
            if msg.audio:
                st.audio(msg.audio, format="audio/wav")
            if msg.error:
                st.caption("⚠ error in response")


# ─────────────────────────────────────────
def _process_voice(client: VoiceAIClient, audio_bytes: bytes):
    """Send voice to LLM → store user + assistant messages."""
    history = [m.to_api_dict() for m in st.session_state.chat_history[-MAX_HISTORY:]]

    resp_audio, resp_text, error = client.chat_with_voice(
        audio_bytes,
        history,
        st.session_state.lang,
        st.session_state.identified_user_id or "guest",
    )

    SessionState.add_message(ChatMessage(role="user", content="🎤 *(voice message)*"))

    if error:
        SessionState.add_message(ChatMessage(role="assistant", content=error, error=True))
    elif resp_text or resp_audio:
        SessionState.add_message(ChatMessage(
            role="assistant",
            content=resp_text or "*(audio response)*",
            audio=resp_audio,
        ))
    else:
        SessionState.add_message(ChatMessage(role="assistant", content="No response received.", error=True))


def enrollment_ui(client: VoiceAIClient):
    """Shown when voice is not recognised."""
    st.markdown("""
    <div class="banner warn">
        🔍 <strong>Voice not recognised.</strong><br>
        Please enter your info and record a short sample so we can remember your voice.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        enroll_id   = st.text_input("User ID (no spaces)", placeholder="e.g. ahmed_01")
    with col2:
        enroll_name = st.text_input("Display Name", placeholder="e.g. Ahmed")

    st.markdown("Record a **5–30 second** voice sample:")
    enroll_audio = st.audio_input("Voice sample", key=f"enroll_{st.session_state.enroll_key}")

    c1, c2 = st.columns([1, 2])
    with c1:
        enroll_btn = st.button("✅ Enroll & Continue", type="primary", use_container_width=True)
    with c2:
        skip_btn = st.button("⏭ Continue as Guest", use_container_width=True)

    if skip_btn:
        st.session_state.identified_user_id = "guest"
        st.session_state.identified_name    = "Guest"
        st.session_state.app_state          = AppState.CHATTING
        st.session_state.enroll_key        += 1
        # Process the pending voice message
        if st.session_state.pending_audio:
            with st.spinner("💬 Processing..."):
                _process_voice(client, st.session_state.pending_audio)
            st.session_state.pending_audio = None
        st.rerun()

    if enroll_btn:
        if not enroll_id or not enroll_name:
            st.error("Please fill in both User ID and Name.")
            return
        sample_bytes = enroll_audio.getvalue() if enroll_audio else st.session_state.pending_audio
        if not sample_bytes:
            st.error("Please record a voice sample first.")
            return

        with st.spinner("Enrolling your voice..."):
            err = client.enroll_voice(sample_bytes, enroll_id, enroll_name)

        if err:
            st.error(f"Enrollment failed: {err}")
            return

        st.session_state.identified_user_id = enroll_id
        st.session_state.identified_name    = enroll_name
        st.session_state.app_state          = AppState.CHATTING
        st.session_state.enroll_key        += 1

        # Process the original voice message that triggered enrollment
        if st.session_state.pending_audio:
            with st.spinner("💬 Processing your message..."):
                _process_voice(client, st.session_state.pending_audio)
            st.session_state.pending_audio = None

        st.rerun()


def voice_input_ui(client: VoiceAIClient):
    """Normal chat: record → identify → chat."""
    st.markdown('<div class="banner info">🎤 Record your voice message below.</div>', unsafe_allow_html=True)

    audio_msg = st.audio_input(
        "Record",
        key=f"voice_{st.session_state.audio_key}",
        label_visibility="collapsed",
    )

    if audio_msg:
        col_send, col_cancel = st.columns([1, 3])
        with col_send:
            send   = st.button("▶ Send", type="primary", use_container_width=True)
        with col_cancel:
            cancel = st.button("✕ Cancel", use_container_width=True)

        if cancel:
            st.session_state.audio_key += 1
            st.rerun()

        if send:
            audio_bytes = audio_msg.getvalue()

            # ── Step 1: identify speaker ──────────────────────────────
            with st.spinner("🔍 Identifying voice..."):
                user_id, id_error = client.identify_voice(audio_bytes)

            if id_error:
                st.error(f"Identification error: {id_error}")
                return

            if not user_id:
                # Unknown → trigger enrollment, keep audio for after enroll
                st.session_state.pending_audio = audio_bytes
                st.session_state.app_state     = AppState.UNKNOWN_USER
                st.session_state.audio_key    += 1
                st.rerun()
                return

            # ── Step 2: store identity ────────────────────────────────
            if st.session_state.identified_user_id != user_id:
                st.session_state.identified_user_id = user_id
                st.session_state.identified_name    = user_id   # extend if API returns a name

            # ── Step 3: chat ──────────────────────────────────────────
            with st.spinner("💬 Processing..."):
                _process_voice(client, audio_bytes)

            st.session_state.audio_key += 1
            st.rerun()


# ─────────────────────────────────────────
def main():
    st.set_page_config(page_title="VoiceAI", page_icon="🎤", layout="wide")
    SessionState.init()
    client = VoiceAIClient(API_URL)

    st.markdown(THEME_CSS, unsafe_allow_html=True)
    render_sidebar()
    render_topbar(client)
    render_chat_history()
    st.divider()

    if st.session_state.app_state == AppState.UNKNOWN_USER:
        enrollment_ui(client)
    else:
        voice_input_ui(client)


if __name__ == "__main__":
    main()
