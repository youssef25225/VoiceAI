import io
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum, auto
from datetime import datetime

import streamlit as st
import soundfile as sf
import requests

# ===== FIX: Define API URL =====
API_URL = "https://yousefemam-voiceai.hf.space"  # Change to your actual API URL
MAX_HISTORY = 20
REQUEST_TIMEOUT = 120
SUPPORTED_LANGS = {"ar": "Arabic", "en": "English", "fr": "French"}


class InputMode(Enum):
    TEXT = auto()
    VOICE = auto()


@dataclass
class ChatMessage:
    role: str
    content: Optional[str] = None
    audio: Optional[bytes] = None
    timestamp: float = field(default_factory=time.time)
    error: bool = False

    def to_api_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content or ""}


# ===== FIX: Define VoiceAIClient BEFORE using it =====
class VoiceAIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "X-Client": "voiceai-streamlit/2.0"
        })

    def health_check(self) -> bool:
        try:
            resp = self.session.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def send_text(self, history: List[Dict], lang: str, user_id: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
        try:
            resp = self.session.post(
                f"{self.base_url}/text",
                json={"history": history, "lang": lang, "user_id": user_id},
                timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
            audio_hex = data.get("audio")
            audio = bytes.fromhex(audio_hex) if audio_hex else None
            text = data.get("reply") or data.get("text") or data.get("response")
            return audio, text, None
        except requests.exceptions.Timeout:
            return None, None, "Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            return None, None, "Cannot connect to server. Please check your connection."
        except Exception as e:
            return None, None, f"Error: {str(e)}"

    def send_voice(self, audio_bytes: bytes, user_id: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
        try:
            files = {"file": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav")}
            resp = self.session.post(
                f"{self.base_url}/voice",
                files=files,
                params={"user_id": user_id},
                timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                return None, None, data["error"]
            audio_hex = data.get("audio")
            audio = bytes.fromhex(audio_hex) if audio_hex else None
            text = data.get("reply") or data.get("text")
            return audio, text, None
        except Exception as e:
            return None, None, f"Error: {str(e)}"


class SessionState:
    @staticmethod
    def init():
        defaults = {
            "chat_history": [],
            "user_id": "default_user",
            "profile": None,
            "input_mode": InputMode.TEXT,
            "audio_key": 0,
            "enroll_key": 0,
            "last_sample": None,
            "lang": "ar",
            "api_status": False,
            "last_health_check": 0,
            "show_export": False,
            "voice_recorded": False,
            "last_request_time": 0,
            "api_error_count": 0,
        }
        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

    @staticmethod
    def clear_chat():
        st.session_state.chat_history = []
        st.session_state.show_export = False
        st.session_state.api_error_count = 0

    @staticmethod
    def add_message(msg: ChatMessage):
        st.session_state.chat_history.append(msg)
        if len(st.session_state.chat_history) > MAX_HISTORY * 2:
            st.session_state.chat_history = st.session_state.chat_history[-MAX_HISTORY * 2:]

    @staticmethod
    def get_message_count() -> int:
        return len(st.session_state.chat_history)


# ===== UI Components =====
THEME_CSS = """
<style>
.stApp { background: #0a0c10; }
.stChatMessage > div:last-child {
    background: #1e1e2e;
    border-radius: 12px;
    padding: 12px 16px;
}
</style>
"""


class UI:
    @staticmethod
    def render_top_bar(user_id: str, mode: InputMode, has_profile: bool, api_online: bool):
        status = "🟢 Online" if api_online else "🔴 Offline"
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; padding: 1rem 0; border-bottom: 1px solid #333;">
            <div>
                <h2 style="margin: 0;">🎤 VoiceAI</h2>
                <small>User: {user_id} | Mode: {"Voice" if mode == InputMode.VOICE else "Text"}</small>
            </div>
            <div>{status}</div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_empty_state():
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <h3>💬 Start a conversation</h3>
            <p>Type a message or use voice input to talk with the assistant.</p>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_voice_banner():
        st.info("🎤 Voice Mode Active - Record your message and click Send")

    @staticmethod
    def render_mode_badge(mode: InputMode):
        if mode == InputMode.TEXT:
            st.caption("✏️ Text Mode")
        else:
            st.caption("🎤 Voice Mode")

    @staticmethod
    def render_chat_message(msg: ChatMessage):
        if msg.role == "assistant" and msg.audio:
            with st.chat_message("assistant"):
                if msg.content:
                    st.markdown(msg.content)
                st.audio(msg.audio, format="audio/wav")
        elif msg.role == "user" and msg.content:
            with st.chat_message("user"):
                st.markdown(msg.content)
        elif msg.role == "assistant" and msg.content:
            with st.chat_message("assistant"):
                st.markdown(msg.content)
                if msg.error:
                    st.error("Error generating response")


def handle_text_input(client: VoiceAIClient):
    prompt = st.chat_input("Message VoiceAI...", key="chat_text_input")
    if prompt and prompt.strip():
        user_msg = ChatMessage(role="user", content=prompt.strip())
        SessionState.add_message(user_msg)

        history = [m.to_api_dict() for m in st.session_state.chat_history[-MAX_HISTORY:]]

        with st.spinner("✨ Generating response..."):
            audio_bytes, text_response, error = client.send_text(
                history, st.session_state.lang, st.session_state.user_id
            )

        if error:
            assistant_msg = ChatMessage(role="assistant", content=error, error=True)
        elif audio_bytes or text_response:
            assistant_msg = ChatMessage(
                role="assistant",
                content=text_response or "Voice response",
                audio=audio_bytes
            )
        else:
            assistant_msg = ChatMessage(role="assistant", content="No response received", error=True)

        SessionState.add_message(assistant_msg)
        st.rerun()


def handle_voice_input(client: VoiceAIClient):
    UI.render_voice_banner()
    audio_msg = st.audio_input(
        "Record your message",
        key=f"voice_{st.session_state.audio_key}",
        label_visibility="collapsed"
    )

    if audio_msg:
        col_send, col_cancel = st.columns([1, 3])
        with col_send:
            send = st.button("Send Voice", use_container_width=True, type="primary")
        with col_cancel:
            cancel = st.button("Cancel", use_container_width=True)

        if cancel:
            st.session_state.audio_key += 1
            st.rerun()

        if send:
            with st.spinner("🎤 Processing..."):
                try:
                    audio_bytes = audio_msg.getvalue()
                    response_audio, response_text, error = client.send_voice(
                        audio_bytes, st.session_state.user_id
                    )

                    if error:
                        st.error(f"❌ {error}")
                        return

                    if response_audio or response_text:
                        assistant_msg = ChatMessage(
                            role="assistant",
                            content=response_text or "Voice response",
                            audio=response_audio
                        )
                        SessionState.add_message(assistant_msg)
                        st.session_state.audio_key += 1
                        st.rerun()
                    else:
                        st.warning("No response received")
                except Exception as e:
                    st.error(f"Error: {str(e)}")


def render_controls(client: VoiceAIClient):
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📝 Text Mode", use_container_width=True):
            st.session_state.input_mode = InputMode.TEXT
            st.rerun()
    with c2:
        if st.button("🎤 Voice Mode", use_container_width=True):
            st.session_state.input_mode = InputMode.VOICE
            st.rerun()
    with c3:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            SessionState.clear_chat()
            st.rerun()


def render_voice_cloning_section():
    with st.expander("🎯 Voice Profile", expanded=not st.session_state.profile):
        new_uid = st.text_input("User ID", value=st.session_state.user_id)
        if new_uid != st.session_state.user_id:
            st.session_state.user_id = new_uid
            st.rerun()

        audio_sample = st.audio_input(
            "Record voice sample (5-30 seconds)",
            key=f"enroll_{st.session_state.enroll_key}"
        )

        if audio_sample:
            st.session_state.last_sample = audio_sample.getvalue()
            st.audio(st.session_state.last_sample, format="audio/wav")

            if st.button("✅ Enroll Voice", type="primary"):
                st.success("Voice enrolled! (Demo mode)")


def main():
    st.set_page_config(page_title="VoiceAI", page_icon="🎤", layout="wide")
    
    SessionState.init()
    client = VoiceAIClient(API_URL)

    st.markdown(THEME_CSS, unsafe_allow_html=True)

    UI.render_top_bar(
        st.session_state.user_id,
        st.session_state.input_mode,
        st.session_state.profile is not None,
        st.session_state.api_status
    )

    render_voice_cloning_section()
    render_controls(client)
    UI.render_mode_badge(st.session_state.input_mode)
    st.divider()

    # Display chat
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            UI.render_chat_message(msg)
    else:
        UI.render_empty_state()

    # Input handling
    if st.session_state.input_mode == InputMode.TEXT:
        handle_text_input(client)
    else:
        handle_voice_input(client)


if __name__ == "__main__":
    main()
