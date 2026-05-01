import io
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum, auto

import streamlit as st
import soundfile as sf
import requests

# Constants
API_URL = "https://yousefemam-voiceai.hf.space"
MAX_HISTORY = 20
REQUEST_TIMEOUT = 120
SUPPORTED_LANGS = {"ar": "العربية", "en": "English", "fr": "Français"}

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

class SessionManager:
    @staticmethod
    def initialize():
        if "initialized" not in st.session_state:
            st.session_state.chat_history = []
            st.session_state.user_id = "user_default"
            st.session_state.profile = None
            st.session_state.input_mode = InputMode.TEXT
            st.session_state.audio_key = 0
            st.session_state.enroll_key = 0
            st.session_state.lang = "ar"
            st.session_state.api_status = True
            st.session_state.theme = "dark"
            st.session_state.initialized = True

    @staticmethod
    def add_message(msg: ChatMessage):
        st.session_state.chat_history.append(msg)
        if len(st.session_state.chat_history) > MAX_HISTORY * 2:
            st.session_state.chat_history = st.session_state.chat_history[-MAX_HISTORY * 2:]

class VoiceAIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def send_text(self, history: List[Dict], lang: str, user_id: str):
        try:
            resp = self.session.post(
                f"{self.base_url}/text",
                json={"history": history, "lang": lang, "user_id": user_id},
                timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
            audio = bytes.fromhex(data["audio"]) if data.get("audio") else None
            return audio, data.get("text") or data.get("response")
        except Exception as e:
            return None, f"Connection Error: {str(e)}"

    def send_voice(self, audio_bytes: bytes, user_id: str):
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
            audio = bytes.fromhex(data["audio"]) if data.get("audio") else None
            return audio, data.get("transcription")
        except Exception as e:
            return None, str(e)

# Integrated Professional CSS
CUSTOM_STYLE = """
<style>
    .stApp { background-color: #0e1117; }
    .main-header {
        padding: 1rem 0;
        border-bottom: 1px solid #30363d;
        margin-bottom: 2rem;
    }
    .chat-container {
        max-width: 800px;
        margin: auto;
    }
    .stChatMessage {
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 10px;
    }
    .status-indicator {
        font-size: 0.8rem;
        padding: 4px 12px;
        border-radius: 15px;
        background: #1f2937;
        color: #9ca3af;
    }
    /* Hide Streamlit components for a cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""

def main():
    st.set_page_config(page_title="VoiceAI Pro", layout="wide")
    st.markdown(CUSTOM_STYLE, unsafe_allow_html=True)
    SessionManager.initialize()
    client = VoiceAIClient(API_URL)

    # Header Section
    col_header, col_status = st.columns([3, 1])
    with col_header:
        st.title("VoiceAI Professional")
    with col_status:
        st.markdown(f'<div class="status-indicator">ID: {st.session_state.user_id} | Mode: {st.session_state.input_mode.name}</div>', unsafe_allow_html=True)

    # Sidebar Settings
    with st.sidebar:
        st.header("Configuration")
        st.session_state.user_id = st.text_input("User Identifier", value=st.session_state.user_id)
        st.session_state.lang = st.selectbox("System Language", options=list(SUPPORTED_LANGS.keys()), format_func=lambda x: SUPPORTED_LANGS[x])
        
        if st.button("Clear Conversation", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    # Chat Display
    for msg in st.session_state.chat_history:
        with st.chat_message(msg.role):
            if msg.content:
                st.markdown(msg.content)
            if msg.audio:
                st.audio(msg.audio, format="audio/wav")

    # Input Logic
    if st.session_state.input_mode == InputMode.TEXT:
        prompt = st.chat_input("Type your message here...")
        if prompt:
            # Add User Message
            user_msg = ChatMessage(role="user", content=prompt)
            SessionManager.add_message(user_msg)
            
            # API Call
            with st.spinner("Processing..."):
                hist = [m.to_api_dict() for m in st.session_state.chat_history]
                audio, text = client.send_text(hist, st.session_state.lang, st.session_state.user_id)
                
                assistant_msg = ChatMessage(role="assistant", content=text, audio=audio)
                SessionManager.add_message(assistant_msg)
                st.rerun()

    else:
        # Voice Mode Implementation
        audio_input = st.audio_input("Record message", key=f"v_{st.session_state.audio_key}")
        if audio_input:
            col1, col2 = st.columns(2)
            if col1.button("Send Recording", use_container_width=True, type="primary"):
                with st.spinner("Analyzing Voice..."):
                    audio_bytes = audio_input.getvalue()
                    resp_audio, transcription = client.send_voice(audio_bytes, st.session_state.user_id)
                    
                    # Add messages
                    SessionManager.add_message(ChatMessage(role="user", content=transcription or "Voice Message"))
                    SessionManager.add_message(ChatMessage(role="assistant", content=None, audio=resp_audio))
                    st.session_state.audio_key += 1
                    st.rerun()
            if col2.button("Discard", use_container_width=True):
                st.session_state.audio_key += 1
                st.rerun()

    # Mode Switcher (Fixed at bottom)
    st.divider()
    m_col1, m_col2 = st.columns(2)
    if m_col1.button("Switch to Text Mode", disabled=st.session_state.input_mode == InputMode.TEXT):
        st.session_state.input_mode = InputMode.TEXT
        st.rerun()
    if m_col2.button("Switch to Voice Mode", disabled=st.session_state.input_mode == InputMode.VOICE):
        st.session_state.input_mode = InputMode.VOICE
        st.rerun()

if __name__ == "__main__":
    main()
