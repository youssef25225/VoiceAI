import io
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple

import streamlit as st
import requests

API_URL = "https://yousefemam-voiceai.hf.space"
MAX_HISTORY = 20
REQUEST_TIMEOUT = 120
SUPPORTED_LANGS = {"ar": "Arabic", "en": "English", "fr": "French"}


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


# ── Main ───────────────────────────────────────────────────────────────────
st.set_page_config(page_title="VoiceAI", page_icon="🎤", layout="wide")
init_state()
client = VoiceAIClient(API_URL)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("VoiceAI 🎤")
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
        st.success(f"Logged in as **{st.session_state.user_name}**")
        st.caption(f"ID: {st.session_state.user_id}")
        st.caption(f"Messages: {len(st.session_state.chat_history)}")
        if st.button("Logout", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.chat_history = []
            st.session_state.audio_key += 1
            st.rerun()
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    else:
        st.caption("Not logged in")

# ── Top: Auth tabs ─────────────────────────────────────────────────────────
if not st.session_state.user_name:
    st.title("Welcome to VoiceAI")
    tab_login, tab_enroll = st.tabs(["🎙 Login with Voice", "📝 Enroll New User"])

    with tab_login:
        audio = st.audio_input("Record your voice", key=f"voice_{st.session_state.audio_key}")
        if st.button("Login", type="primary", use_container_width=True, key="login_submit"):
            if not audio:
                st.warning("Please record your voice first.")
            else:
                with st.spinner("Identifying your voice..."):
                    uid, uname, err = client.identify(audio.getvalue())
                if err:
                    st.error(err)
                elif not uid:
                    st.warning("Voice not recognised. Please enroll first.")
                else:
                    st.session_state.user_id   = uid
                    st.session_state.user_name = uname or uid
                    st.rerun()

    with tab_enroll:
        col1, col2 = st.columns(2)
        with col1:
            uid  = st.text_input("User ID (no spaces)", placeholder="e.g. ahmed_01")
        with col2:
            name = st.text_input("Display Name", placeholder="e.g. Ahmed")
        sample = st.audio_input("Voice sample (5–30 sec)", key=f"enroll_{st.session_state.enroll_key}")
        if st.button("Enroll and Login", type="primary", use_container_width=True, key="enroll_submit"):
            if not uid or not name:
                st.warning("Please fill in User ID and Name.")
            elif not sample:
                st.warning("Please record a voice sample first.")
            else:
                with st.spinner("Enrolling your voice..."):
                    err = client.enroll(sample.getvalue(), uid, name)
                if err:
                    st.error(f"Enrollment failed: {err}")
                else:
                    st.session_state.user_id   = uid
                    st.session_state.user_name = name
                    st.rerun()

    st.divider()

# ── Bottom: Chat ───────────────────────────────────────────────────────────
if st.session_state.user_name:
    st.title(f"Hello, {st.session_state.user_name} 👋")

if st.session_state.chat_history:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg.role):
            st.markdown(msg.content)
            if msg.audio:
                st.audio(msg.audio, format="audio/mp3", autoplay=True)
            if msg.error:
                st.caption("⚠ error")

if st.session_state.user_name:
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
else:
    st.chat_input("Login first to start chatting...", disabled=True)
