import io
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from enum import Enum, auto

import streamlit as st
import requests

API_URL = "https://yousefemam-voiceai.hf.space"
MAX_HISTORY = 20
REQUEST_TIMEOUT = 120
SUPPORTED_LANGS = {"ar": "Arabic", "en": "English", "fr": "French"}


class AppState(Enum):
    LANDING    = auto()
    ENROLLING  = auto()
    LOGGING_IN = auto()
    CHATTING   = auto()


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
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def health_check(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/health", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def enroll(self, audio_bytes: bytes, user_id: str, name: str) -> Optional[str]:
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

    def chat(self, history: List[Dict], lang: str, user_id: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
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
            text = data.get("reply") or data.get("text") or data.get("response")
            return audio, text, None
        except requests.exceptions.Timeout:
            return None, None, "Request timed out."
        except requests.exceptions.ConnectionError:
            return None, None, "Cannot connect to server."
        except Exception as e:
            return None, None, str(e)


def init_state():
    defaults = {
        "app_state":    AppState.LANDING,
        "user_id":      None,
        "user_name":    None,
        "chat_history": [],
        "lang":         "ar",
        "audio_key":    0,
        "enroll_key":   0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def add_msg(msg: ChatMessage):
    st.session_state.chat_history.append(msg)
    if len(st.session_state.chat_history) > MAX_HISTORY * 2:
        st.session_state.chat_history = st.session_state.chat_history[-MAX_HISTORY * 2:]


@st.cache_data(ttl=30, show_spinner=False)
def cached_health_check(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def render_sidebar():
    with st.sidebar:
        st.title("VoiceAI")
        st.divider()

        online = cached_health_check(API_URL)
        if online:
            st.success("API online")
        else:
            st.error("API offline")

        st.divider()

        lang_keys = list(SUPPORTED_LANGS.keys())
        lang_vals  = list(SUPPORTED_LANGS.values())
        idx = lang_keys.index(st.session_state.lang)
        sel = st.selectbox("Language", lang_vals, index=idx)
        new_lang = lang_keys[lang_vals.index(sel)]
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()

        st.divider()

        if st.session_state.user_name:
            st.write(f"Logged in as: **{st.session_state.user_name}**")
            st.caption(f"ID: {st.session_state.user_id}")
            st.caption(f"Messages: {len(st.session_state.chat_history)}")
            if st.button("Logout", use_container_width=True):
                st.session_state.user_id    = None
                st.session_state.user_name  = None
                st.session_state.app_state  = AppState.LANDING
                st.session_state.chat_history = []
                st.rerun()
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
        else:
            st.caption("Not logged in")


def screen_landing():
    st.title("Welcome to VoiceAI")
    st.write("Voice authentication · Text chat · TTS responses")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Returning User")
        st.write("Already enrolled? Record your voice to log in.")
        if st.button("Login with Voice", use_container_width=True, type="primary", key="btn_login"):
            st.session_state.app_state = AppState.LOGGING_IN
            st.session_state.audio_key += 1
            st.rerun()
    with col2:
        st.subheader("New User")
        st.write("First time? Register your voice print now.")
        if st.button("Enroll My Voice", use_container_width=True, key="btn_enroll"):
            st.session_state.app_state = AppState.ENROLLING
            st.session_state.enroll_key += 1
            st.rerun()


def screen_enroll(client: VoiceAIClient):
    st.title("New User Enrollment")
    if st.button("← Back", key="enroll_back"):
        st.session_state.app_state = AppState.LANDING
        st.rerun()
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        uid  = st.text_input("User ID (no spaces)", placeholder="e.g. ahmed_01")
    with col2:
        name = st.text_input("Display Name", placeholder="e.g. Ahmed")
    st.write("Record a clear voice sample (5–30 seconds):")
    sample = st.audio_input("Voice sample", key=f"enroll_{st.session_state.enroll_key}")
    if st.button("Enroll and Login", type="primary", use_container_width=True, key="enroll_submit"):
        if not uid or not name:
            st.warning("Please fill in User ID and Name.")
            return
        if not sample:
            st.warning("Please record a voice sample first.")
            return
        with st.spinner("Enrolling your voice..."):
            err = client.enroll(sample.getvalue(), uid, name)
        if err:
            st.error(f"Enrollment failed: {err}")
        else:
            st.session_state.user_id   = uid
            st.session_state.user_name = name
            st.session_state.app_state = AppState.CHATTING
            st.rerun()


def screen_login(client: VoiceAIClient):
    st.title("Voice Login")
    if st.button("← Back", key="login_back"):
        st.session_state.app_state = AppState.LANDING
        st.rerun()
    st.divider()
    audio = st.audio_input("Record your voice", key=f"voice_{st.session_state.audio_key}")
    if st.button("Login", type="primary", use_container_width=True, key="login_submit"):
        if not audio:
            st.warning("Please record your voice first.")
            return
        with st.spinner("Identifying your voice..."):
            uid, uname, err = client.identify(audio.getvalue())
        if err:
            st.error(err)
            return
        if not uid:
            st.warning("Voice not recognised. Haven't enrolled yet? Go back and choose Enroll My Voice.")
            return
        st.session_state.user_id   = uid
        st.session_state.user_name = uname or uid
        st.session_state.app_state = AppState.CHATTING
        st.rerun()


def screen_chat(client: VoiceAIClient):
    st.title(f"Hello, {st.session_state.user_name}")
    if not st.session_state.chat_history:
        st.write("Type your message below — replies will be spoken aloud.")
    else:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg.role):
                st.markdown(msg.content)
                if msg.audio:
                    st.audio(msg.audio, format="audio/wav", autoplay=True)
                if msg.error:
                    st.caption("⚠ error")

    prompt = st.chat_input("Type your message...")
    if prompt and prompt.strip():
        add_msg(ChatMessage(role="user", content=prompt.strip()))
        history = [m.to_api_dict() for m in st.session_state.chat_history[-MAX_HISTORY:]]
        with st.spinner("Generating response..."):
            audio_bytes, text_reply, error = client.chat(
                history, st.session_state.lang, st.session_state.user_id
            )
        if error:
            add_msg(ChatMessage(role="assistant", content=error, error=True))
        elif audio_bytes or text_reply:
            add_msg(ChatMessage(role="assistant", content=text_reply or "*(voice response)*", audio=audio_bytes))
        else:
            add_msg(ChatMessage(role="assistant", content="No response received.", error=True))
        st.rerun()


# ── Main ───────────────────────────────────────────────────────────────────
st.set_page_config(page_title="VoiceAI", page_icon="🎤", layout="wide")
init_state()
client = VoiceAIClient(API_URL)
render_sidebar()

state = st.session_state.app_state
if state == AppState.LANDING:
    screen_landing()
elif state == AppState.ENROLLING:
    screen_enroll(client)
elif state == AppState.LOGGING_IN:
    screen_login(client)
elif state == AppState.CHATTING:
    screen_chat(client)
