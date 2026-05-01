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


class AppState(Enum):
    LANDING    = auto()   # not logged in → choose login or enroll
    ENROLLING  = auto()   # new user recording voice sample
    LOGGING_IN = auto()   # returning user recording voice to login
    CHATTING   = auto()   # logged in → text in, TTS out


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

    def enroll(self, audio_bytes: bytes, user_id: str, name: str) -> Optional[str]:
        """POST /enroll → {"status":"ok"} | returns error string or None"""
        try:
            files = {"file": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")}
            r = self.session.post(
                f"{self.base_url}/enroll",
                files=files,
                data={"user_id": user_id, "name": name},
                timeout=REQUEST_TIMEOUT,
            )
            r.raise_for_status()
            return r.json().get("error")
        except Exception as e:
            return str(e)

    def identify(self, audio_bytes: bytes) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """POST /identify → {"user_id":"...","name":"..."} | returns (user_id, name, error)"""
        try:
            files = {"file": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")}
            r = self.session.post(f"{self.base_url}/identify", files=files, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json()
            if "error" in data:
                return None, None, data["error"]
            return data.get("user_id"), data.get("name"), None
        except requests.exceptions.Timeout:
            return None, None, "Request timed out."
        except requests.exceptions.ConnectionError:
            return None, None, "Cannot connect to server."
        except Exception as e:
            return None, None, str(e)

    def chat(
        self, history: List[Dict], lang: str, user_id: str
    ) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
        """POST /text → {"reply":"...","audio":"<hex>"} | returns (audio_bytes, text, error)"""
        try:
            r = self.session.post(
                f"{self.base_url}/text",
                json={"history": history, "lang": lang, "user_id": user_id},
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


# ─────────────────────────────────────────
class SS:
    @staticmethod
    def init():
        defaults = {
            "app_state":    AppState.LANDING,
            "user_id":      None,
            "user_name":    None,
            "chat_history": [],
            "lang":         "ar",
            "api_status":   False,
            "last_hc":      0,
            "audio_key":    0,
            "enroll_key":   0,
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

    @staticmethod
    def logout():
        st.session_state.user_id      = None
        st.session_state.user_name    = None
        st.session_state.app_state    = AppState.LANDING
        st.session_state.chat_history = []
        st.session_state.audio_key   += 1

    @staticmethod
    def add_msg(msg: ChatMessage):
        st.session_state.chat_history.append(msg)
        if len(st.session_state.chat_history) > MAX_HISTORY * 2:
            st.session_state.chat_history = st.session_state.chat_history[-MAX_HISTORY * 2:]


# ─────────────────────────────────────────
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Outfit:wght@300;400;600;700&display=swap');

html, body, .stApp { background: #07090e !important; font-family: 'Outfit', sans-serif; }
section[data-testid="stSidebar"] { background: #0b0d14 !important; border-right: 1px solid #141828; }

.topbar {
    display:flex; justify-content:space-between; align-items:center;
    padding:1rem 0 1.2rem; border-bottom:1px solid #141828; margin-bottom:1.4rem;
}
.topbar-brand { font-size:1.25rem; font-weight:700; color:#e0e4f4; letter-spacing:-.03em; }
.topbar-sub   { font-family:'JetBrains Mono',monospace; font-size:.67rem; color:#3a3e56; margin-top:3px; }
.pill {
    font-family:'JetBrains Mono',monospace; font-size:.65rem;
    padding:3px 11px; border-radius:100px;
    background:#0b0d14; border:1px solid #1c2030; color:#505570;
}
.pill.on   { color:#4ade80; border-color:#14532d; background:#060e08; }
.pill.user { color:#818cf8; border-color:#2a2d5a; background:#09091c; }

.card { border-radius:12px; padding:2rem; border:1px solid #141828; background:#0b0d14; margin-bottom:1.2rem; }
.card h3 { font-size:1.05rem; font-weight:600; color:#c8cce4; margin:0 0 .5rem; }
.card p  { font-size:.82rem; color:#505570; margin:0; font-family:'JetBrains Mono',monospace; }

.banner { border-radius:10px; padding:12px 16px; margin-bottom:1rem; font-size:.83rem; border:1px solid; }
.banner.warn    { background:#140f00; border-color:#3d2e00; color:#d4a017; }
.banner.info    { background:#07101a; border-color:#1a3050; color:#60a5fa; }
.banner.success { background:#060e08; border-color:#14532d; color:#4ade80; }
.banner.err     { background:#140707; border-color:#5a1414; color:#f87171; }

.choice-row { display:flex; gap:1rem; }
.choice-box {
    flex:1; border-radius:12px; padding:1.6rem 1.2rem;
    border:1px solid #141828; background:#0b0d14; text-align:center;
    transition:border-color .15s;
}
.choice-box .icon { font-size:2.2rem; display:block; margin-bottom:.6rem; }
.choice-box h4    { font-size:.9rem; font-weight:600; color:#c8cce4; margin:0 0 .35rem; }
.choice-box p     { font-size:.73rem; color:#404560; font-family:'JetBrains Mono',monospace; margin:0; }

div[data-testid="stChatMessage"] > div:last-child {
    background:#0b0d14 !important; border:1px solid #141828 !important;
    border-radius:10px !important; padding:10px 14px !important;
    color:#b8bcd4 !important; font-size:.87rem !important;
}

.empty { text-align:center; padding:3.5rem 1rem; }
.empty h3 { font-size:.95rem; color:#303450; font-weight:600; margin-bottom:.4rem; }
.empty p  { font-family:'JetBrains Mono',monospace; font-size:.72rem; color:#252840; }

.stTextInput input, div[data-baseweb="select"] * {
    background:#0b0d14 !important; border-color:#1c2030 !important;
    color:#c8cce4 !important; font-family:'JetBrains Mono',monospace !important;
    font-size:.82rem !important; border-radius:8px !important;
}
div[data-testid="stChatInput"] textarea {
    background:#0b0d14 !important; border:1px solid #1c2030 !important;
    color:#c8cce4 !important; border-radius:10px !important; font-family:'Outfit',sans-serif !important;
}
.stButton > button {
    background:#0b0d14 !important; border:1px solid #1c2030 !important;
    color:#707590 !important; border-radius:8px !important;
    font-family:'JetBrains Mono',monospace !important; font-size:.77rem !important; transition:all .15s !important;
}
.stButton > button:hover { border-color:#3a3e60 !important; color:#c8cce4 !important; background:#10121e !important; }
button[kind="primary"] { background:#1a2060 !important; border-color:#2a30a0 !important; color:#a0b0ff !important; }
.stDivider { border-color:#141828 !important; }
small, .stCaption { color:#383c54 !important; font-family:'JetBrains Mono',monospace !important; font-size:.68rem !important; }
</style>
"""


# ─────────────────────────────────────────  shared layout

def render_topbar(client: VoiceAIClient):
    now = time.time()
    if now - st.session_state.last_hc > 60:
        st.session_state.api_status = client.health_check()
        st.session_state.last_hc    = now

    api_cls = "on"   if st.session_state.api_status else ""
    api_lbl = "● api online" if st.session_state.api_status else "● api offline"
    user_lbl = f"👤 {st.session_state.user_name}" if st.session_state.user_name else "👤 not logged in"
    user_cls = "user" if st.session_state.user_name else ""

    st.markdown(f"""
    <div class="topbar">
      <div>
        <div class="topbar-brand">🎤 VoiceAI</div>
        <div class="topbar-sub">voice-auth · text-in · tts-out</div>
      </div>
      <div style="display:flex;gap:8px;align-items:center;">
        <span class="pill {user_cls}">{user_lbl}</span>
        <span class="pill {api_cls}">{api_lbl}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.divider()

        lang_keys = list(SUPPORTED_LANGS.keys())
        lang_vals = list(SUPPORTED_LANGS.values())
        idx = lang_keys.index(st.session_state.lang) if st.session_state.lang in lang_keys else 0
        sel = st.selectbox("Language", lang_vals, index=idx)
        new_lang = lang_keys[lang_vals.index(sel)]
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()

        st.divider()
        if st.session_state.user_name:
            st.caption(f"User : {st.session_state.user_name}")
            st.caption(f"ID   : {st.session_state.user_id}")
            st.caption(f"Msgs : {len(st.session_state.chat_history)}")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                SS.logout()
                st.rerun()
            if st.button("🗑 Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        else:
            st.caption("Not logged in")


# ─────────────────────────────────────────  screens

def screen_landing():
    st.markdown("""
    <div class="card">
      <h3>Welcome to VoiceAI</h3>
      <p>voice authentication  ·  text chat  ·  tts responses</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="choice-box">
          <span class="icon">🔑</span>
          <h4>Login</h4>
          <p>Already enrolled?<br>Record your voice to log in.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Login with Voice", use_container_width=True, type="primary"):
            st.session_state.app_state  = AppState.LOGGING_IN
            st.session_state.audio_key += 1
            st.rerun()

    with col2:
        st.markdown("""
        <div class="choice-box">
          <span class="icon">✨</span>
          <h4>New User</h4>
          <p>First time?<br>Register your voice print now.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enroll My Voice", use_container_width=True):
            st.session_state.app_state   = AppState.ENROLLING
            st.session_state.enroll_key += 1
            st.rerun()


def screen_enroll(client: VoiceAIClient):
    st.markdown('<div class="banner info">✨ <strong>New user enrollment</strong> — one-time setup.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        uid  = st.text_input("User ID (no spaces)", placeholder="e.g. ahmed_01")
    with col2:
        name = st.text_input("Display Name", placeholder="e.g. Ahmed")

    st.markdown("🎙️ Record a clear voice sample **(5–30 seconds):**")
    sample = st.audio_input("Voice sample", key=f"enroll_{st.session_state.enroll_key}")

    c1, c2 = st.columns([2, 1])
    with c1:
        ok   = st.button("✅ Enroll & Login", type="primary", use_container_width=True)
    with c2:
        back = st.button("← Back", use_container_width=True)

    if back:
        st.session_state.app_state = AppState.LANDING
        st.rerun()

    if ok:
        if not uid or not name:
            st.markdown('<div class="banner warn">⚠ Please fill in User ID and Name.</div>', unsafe_allow_html=True)
            return
        if not sample:
            st.markdown('<div class="banner warn">⚠ Please record a voice sample first.</div>', unsafe_allow_html=True)
            return

        with st.spinner("Enrolling your voice..."):
            err = client.enroll(sample.getvalue(), uid, name)

        if err:
            st.markdown(f'<div class="banner err">❌ Enrollment failed: {err}</div>', unsafe_allow_html=True)
        else:
            st.session_state.user_id   = uid
            st.session_state.user_name = name
            st.session_state.app_state = AppState.CHATTING
            st.rerun()


def screen_login(client: VoiceAIClient):
    st.markdown('<div class="banner info">🔑 <strong>Voice Login</strong> — record a short clip to identify yourself.</div>', unsafe_allow_html=True)

    audio = st.audio_input("Record your voice", key=f"voice_{st.session_state.audio_key}", label_visibility="collapsed")

    c1, c2 = st.columns([2, 1])
    with c1:
        ok   = st.button("🔑 Login", type="primary", use_container_width=True)
    with c2:
        back = st.button("← Back", use_container_width=True)

    if back:
        st.session_state.app_state = AppState.LANDING
        st.rerun()

    if ok:
        if not audio:
            st.markdown('<div class="banner warn">⚠ Please record your voice first.</div>', unsafe_allow_html=True)
            return

        with st.spinner("🔍 Identifying your voice..."):
            uid, uname, err = client.identify(audio.getvalue())

        if err:
            st.markdown(f'<div class="banner err">❌ {err}</div>', unsafe_allow_html=True)
            return

        if not uid:
            st.markdown("""
            <div class="banner warn">
              🤷 <strong>Voice not recognised.</strong><br>
              Haven't enrolled yet? Go back and choose "New User".
            </div>
            """, unsafe_allow_html=True)
            return

        st.session_state.user_id   = uid
        st.session_state.user_name = uname or uid
        st.session_state.app_state = AppState.CHATTING
        st.rerun()


def screen_chat(client: VoiceAIClient):
    # ── history ───────────────────────────────────────────────
    if not st.session_state.chat_history:
        st.markdown(f"""
        <div class="empty">
          <h3>Hello, {st.session_state.user_name} 👋</h3>
          <p>Type your message below — replies will be spoken aloud.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg.role):
                st.markdown(msg.content)
                if msg.audio:
                    st.audio(msg.audio, format="audio/wav", autoplay=True)
                if msg.error:
                    st.caption("⚠ error")

    # ── input ─────────────────────────────────────────────────
    prompt = st.chat_input("Type your message…")
    if prompt and prompt.strip():
        SS.add_msg(ChatMessage(role="user", content=prompt.strip()))

        history = [m.to_api_dict() for m in st.session_state.chat_history[-MAX_HISTORY:]]

        with st.spinner("💬 Generating response..."):
            audio_bytes, text_reply, error = client.chat(
                history, st.session_state.lang, st.session_state.user_id
            )

        if error:
            SS.add_msg(ChatMessage(role="assistant", content=error, error=True))
        elif audio_bytes or text_reply:
            SS.add_msg(ChatMessage(
                role="assistant",
                content=text_reply or "*(voice response)*",
                audio=audio_bytes,
            ))
        else:
            SS.add_msg(ChatMessage(role="assistant", content="No response received.", error=True))

        st.rerun()


# ─────────────────────────────────────────
def main():
    st.set_page_config(page_title="VoiceAI", page_icon="🎤", layout="wide")
    SS.init()
    client = VoiceAIClient(API_URL)

    st.markdown(THEME_CSS, unsafe_allow_html=True)
    render_sidebar()
    render_topbar(client)

    state = st.session_state.app_state
    try:
        if state == AppState.LANDING:
            screen_landing()
        elif state == AppState.ENROLLING:
            screen_enroll(client)
        elif state == AppState.LOGGING_IN:
            screen_login(client)
        elif state == AppState.CHATTING:
            screen_chat(client)
    except Exception as e:
        import traceback
        st.error(f"Error: {e}")
        st.code(traceback.format_exc())


main()
