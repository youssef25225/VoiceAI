import io
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum, auto

import streamlit as st
import soundfile as sf
import requests

API_URL = "https://yousefemam-voiceai.hf.space"
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
        }
        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

    @staticmethod
    def clear_chat():
        st.session_state.chat_history = []
        st.session_state.show_export = False

    @staticmethod
    def add_message(msg: ChatMessage):
        st.session_state.chat_history.append(msg)
        if len(st.session_state.chat_history) > MAX_HISTORY * 2:
            st.session_state.chat_history = st.session_state.chat_history[-MAX_HISTORY * 2:]


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

    def send_text(self, history: List[Dict], lang: str, user_id: str) -> Tuple[Optional[bytes], Optional[str]]:
        resp = self.session.post(
            f"{self.base_url}/text",
            json={"history": history, "lang": lang, "user_id": user_id},
            timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
        audio_hex = data.get("audio")
        audio = bytes.fromhex(audio_hex) if audio_hex else None
        text = data.get("text") or data.get("response") or data.get("message")
        return audio, text

    def send_voice(self, audio_bytes: bytes, user_id: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
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
        text = data.get("text") or data.get("response") or data.get("message")
        return audio, text, None


class VoiceProfileManager:
    @staticmethod
    def load_profile(user_id: str) -> Optional[Any]:
        try:
            from src.core.enroll import load_voice_profile
            return load_voice_profile(user_id)
        except ImportError:
            return None

    @staticmethod
    def save_profile(user_id: str, audio_data: Any, sample_rate: int) -> Any:
        from src.core.enroll import save_voice_profile
        return save_voice_profile(user_id, audio_data, sample_rate)


THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

.stApp {
    --bg: #0a0c10;
    --surface: #111318;
    --surface-elevated: #161922;
    --surface-hover: #1c2030;
    --border: #1e2330;
    --border-active: #2a3148;
    --accent: #6366f1;
    --accent-light: #818cf8;
    --accent-dim: rgba(99,102,241,0.08);
    --accent-glow: rgba(99,102,241,0.25);
    --text: #e2e5ec;
    --text-secondary: #8b92a8;
    --text-muted: #5a6078;
    --success: #34d399;
    --warning: #fbbf24;
    --error: #f87171;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
    --shadow: 0 4px 24px rgba(0,0,0,0.4);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.5);
    --topbar-bg: rgba(10, 12, 16, 0.85);
}

* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.stApp { background: var(--bg) !important; }

.MainMenu, footer, header { display: none !important; }

.block-container {
    padding: 2rem 1.5rem 8rem !important;
    max-width: 800px !important;
    margin: 0 auto !important;
}

[data-testid="stSidebar"] { display: none !important; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: var(--border-active);
    border-radius: 99px;
}
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

.top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 0;
    margin-bottom: 2rem;
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(12px);
    background: var(--topbar-bg);
}

.brand {
    display: flex;
    gap: 14px;
    align-items: center;
}

.brand-icon {
    width: 42px;
    height: 42px;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--accent), #a78bfa);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 30px var(--accent-glow);
    font-size: 1.25rem;
    font-weight: 700;
    color: white;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.brand-icon:hover { transform: scale(1.05) rotate(-3deg); }

.brand-name {
    font-family: 'Playfair Display', serif !important;
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.2;
    color: var(--text) !important;
}
.brand-sub {
    font-size: 0.75rem;
    color: var(--text-secondary) !important;
    font-weight: 400;
    letter-spacing: 0.02em;
}

.status-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    font-weight: 500;
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 8px 16px;
    border-radius: 99px;
    color: var(--text-secondary);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.status-pill:hover {
    border-color: var(--border-active);
    background: var(--surface-elevated);
}

.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    position: relative;
}
.status-dot::after {
    content: '';
    position: absolute;
    inset: -2px;
    border-radius: 50%;
    animation: pulse 2s infinite;
}
.status-dot.online { background: var(--success); }
.status-dot.online::after { background: var(--success); opacity: 0.3; }
.status-dot.offline { background: var(--error); }
.status-dot.offline::after { background: var(--error); opacity: 0.3; }
.status-dot.unknown { background: var(--warning); }

@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(2); opacity: 0; }
}

[data-testid="stChatMessage"] {
    background: transparent !important;
    padding: 0.5rem 0 !important;
}

.stChatMessage > div:last-child {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 16px 20px !important;
    max-width: 85% !important;
    color: var(--text) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.stChatMessage > div:last-child:hover {
    box-shadow: var(--shadow) !important;
    border-color: var(--border-active) !important;
}

.stChatMessage p, .stChatMessage span, .stChatMessage div {
    color: var(--text) !important;
    line-height: 1.6 !important;
}

[data-testid="stChatMessageContent"] * { color: var(--text) !important; }

div[data-testid="stChatMessage"]:has(svg[data-testid="chatAvatarIcon-user"]) .stChatMessage > div:last-child {
    background: var(--surface-elevated) !important;
    border-color: var(--border-active) !important;
    border-bottom-right-radius: 4px !important;
}
div[data-testid="stChatMessage"]:has(svg[data-testid="chatAvatarIcon-assistant"]) .stChatMessage > div:last-child {
    border-bottom-left-radius: 4px !important;
}

[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 1.5rem !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    max-width: 760px !important;
    width: calc(100% - 3rem) !important;
    z-index: 50;
}
[data-testid="stChatInput"] textarea {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 16px !important;
    padding: 14px 18px !important;
    font-size: 0.95rem !important;
    box-shadow: var(--shadow) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 4px var(--accent-dim), var(--shadow) !important;
    outline: none !important;
}

.stButton > button {
    background: var(--surface-elevated) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text-secondary) !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}
.stButton > button:hover {
    background: var(--accent) !important;
    color: white !important;
    border-color: var(--accent) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px var(--accent-glow);
}
.stButton > button:active { transform: translateY(0); }

.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: white !important;
    border-color: var(--accent) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--accent-light) !important;
    border-color: var(--accent-light) !important;
}

audio {
    width: 100% !important;
    border-radius: 8px !important;
    margin-top: 8px;
}
audio::-webkit-media-controls-panel {
    background: var(--surface-elevated) !important;
}

.voice-banner {
    background: var(--accent-dim);
    border: 1.5px solid var(--accent-glow);
    padding: 14px 18px;
    border-radius: 12px;
    color: var(--accent-light);
    font-weight: 500;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1rem;
    animation: slideIn 0.3s ease-out;
}

.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    animation: fadeIn 0.5s ease-out;
}
.empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
    animation: float 3s ease-in-out infinite;
}
.empty-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text) !important;
    margin-bottom: 0.5rem;
}
.empty-sub {
    font-size: 0.9rem;
    color: var(--text-secondary) !important;
    max-width: 300px;
    margin: 0 auto;
    line-height: 1.5;
}

.stExpander {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    background: var(--surface) !important;
    overflow: hidden;
}
.stExpander > details > summary {
    background: var(--surface-elevated) !important;
    padding: 14px 18px !important;
    font-weight: 500 !important;
    color: var(--text) !important;
}
.stExpander > details > summary:hover {
    background: var(--surface-hover) !important;
}

.stTextInput > div > div > input {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-dim) !important;
}

.stSelectbox > div > div {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
}
.stSelectbox > div > div > div {
    color: var(--text) !important;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.01em;
}
.badge-dot { width: 5px; height: 5px; border-radius: 50%; }

.divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.5rem 0;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes slideIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

.stToast {
    background: var(--surface-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}

.stSpinner > div {
    border-color: var(--accent) !important;
    border-top-color: transparent !important;
}

.msg-timestamp {
    font-size: 0.7rem;
    color: var(--text-muted) !important;
    margin-top: 6px;
    text-align: right;
}

[data-testid="stAudioInput"] {
    background: var(--surface) !important;
    border: 1.5px dashed var(--border-active) !important;
    border-radius: 12px !important;
    padding: 20px !important;
}
[data-testid="stAudioInput"]:hover {
    border-color: var(--accent) !important;
    background: var(--accent-dim) !important;
}

.stAlert {
    background: var(--surface-elevated) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 12px !important;
}
.stAlert [data-testid="stMarkdownContainer"] p {
    color: var(--text) !important;
}
</style>
"""


class UI:
    @staticmethod
    def render_top_bar(user_id: str, mode: InputMode, has_profile: bool, api_online: bool):
        mode_str = "Text" if mode == InputMode.TEXT else "Voice"
        profile_str = "Voice Cloned" if has_profile else "Default Voice"
        status_class = "online" if api_online else "offline"
        status_text = "Online" if api_online else "Offline"

        st.html(f"""
        <div class="top-bar">
            <div class="brand">
                <div class="brand-icon">V</div>
                <div>
                    <div class="brand-name">VoiceAI</div>
                    <div class="brand-sub">Intelligent Voice Assistant</div>
                </div>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <div class="status-pill">
                    <span class="status-dot {status_class}"></span>
                    <span>{status_text}</span>
                    <span style="color: var(--text-muted); margin: 0 4px;">|</span>
                    <span>{user_id}</span>
                    <span style="color: var(--text-muted); margin: 0 4px;">|</span>
                    <span>{mode_str}</span>
                    <span style="color: var(--text-muted); margin: 0 4px;">|</span>
                    <span>{profile_str}</span>
                </div>
            </div>
        </div>
        """)

    @staticmethod
    def render_empty_state():
        st.html("""
        <div class="empty-state">
            <div class="empty-icon">+</div>
            <div class="empty-title">Start a conversation</div>
            <div class="empty-sub">Type a message or switch to Voice Mode to speak naturally with the assistant.</div>
        </div>
        """)

    @staticmethod
    def render_voice_banner():
        st.html("""
        <div class="voice-banner">
            Voice Mode Active - Record your message and press Send
        </div>
        """)

    @staticmethod
    def render_mode_badge(mode: InputMode):
        color = "var(--accent)"
        label = "Text Mode Active" if mode == InputMode.TEXT else "Voice Mode Active"
        icon = "T" if mode == InputMode.TEXT else "V"
        st.html(f"""
        <div class="badge" style="margin-top:12px; border: 1.5px solid {color}33; background: {color}10; color: {color};">
            <span class="badge-dot" style="background:{color}; box-shadow:0 0 6px {color}80;"></span>
            {icon} {label}
        </div>
        """)

    @staticmethod
    def format_timestamp(ts: float) -> str:
        from datetime import datetime
        return datetime.fromtimestamp(ts).strftime("%H:%M")

    @staticmethod
    def render_chat_message(msg: ChatMessage):
        if msg.role == "assistant" and msg.audio:
            with st.chat_message("assistant"):
                if msg.content:
                    st.markdown(msg.content)
                st.audio(msg.audio, format="audio/wav")
                st.html(f'<div class="msg-timestamp">{UI.format_timestamp(msg.timestamp)}</div>')
        elif msg.role == "user" and msg.content:
            with st.chat_message("user"):
                st.markdown(msg.content)
                st.html(f'<div class="msg-timestamp">{UI.format_timestamp(msg.timestamp)}</div>')
        elif msg.role == "assistant" and msg.content:
            with st.chat_message("assistant"):
                st.markdown(msg.content)
                if msg.error:
                    st.error("An error occurred generating the response.")
                st.html(f'<div class="msg-timestamp">{UI.format_timestamp(msg.timestamp)}</div>')


def handle_text_input(client: VoiceAIClient):
    prompt = st.chat_input("Message VoiceAI...", key="chat_text_input")
    if prompt and prompt.strip():
        user_msg = ChatMessage(role="user", content=prompt.strip())
        SessionState.add_message(user_msg)

        history = [
            m.to_api_dict()
            for m in st.session_state.chat_history[-MAX_HISTORY:]
        ]

        try:
            with st.spinner("Generating response..."):
                audio_bytes, text_response = client.send_text(
                    history,
                    st.session_state.lang,
                    st.session_state.user_id
                )

            if audio_bytes or text_response:
                assistant_msg = ChatMessage(
                    role="assistant",
                    content=text_response or "Voice response generated",
                    audio=audio_bytes
                )
            else:
                assistant_msg = ChatMessage(
                    role="assistant",
                    content="I could not generate a response. Please try again.",
                    error=True
                )

        except requests.exceptions.Timeout:
            assistant_msg = ChatMessage(
                role="assistant",
                content="Request timed out. The server might be busy.",
                error=True
            )
        except requests.exceptions.ConnectionError:
            assistant_msg = ChatMessage(
                role="assistant",
                content="Cannot connect to the VoiceAI server. Please check your connection.",
                error=True
            )
        except Exception as e:
            assistant_msg = ChatMessage(
                role="assistant",
                content=f"An unexpected error occurred: {str(e)}",
                error=True
            )

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
            send = st.button("Send Voice", use_container_width=True, type="primary", key="send_voice_btn")
        with col_cancel:
            cancel = st.button("Cancel", use_container_width=True, key="cancel_voice_btn")

        if cancel:
            st.session_state.audio_key += 1
            st.session_state.voice_recorded = False
            st.rerun()

        if send:
            with st.spinner("Transcribing and generating response..."):
                try:
                    audio_bytes = audio_msg.getvalue()
                    response_audio, response_text, error = client.send_voice(
                        audio_bytes,
                        st.session_state.user_id
                    )

                    if error:
                        st.error(f"Error: {error}")
                        return

                    if response_audio or response_text:
                        assistant_msg = ChatMessage(
                            role="assistant",
                            content=response_text or "Voice response generated",
                            audio=response_audio
                        )
                        SessionState.add_message(assistant_msg)
                        st.session_state.audio_key += 1
                        st.session_state.voice_recorded = False
                        st.rerun()
                    else:
                        st.warning("No response received from the server.")

                except requests.exceptions.Timeout:
                    st.error("Request timed out. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error("Connection failed. Please check your internet.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")


def render_controls(client: VoiceAIClient):
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([1, 1, 1, 1])

    with ctrl1:
        btn_type = "primary" if st.session_state.input_mode == InputMode.TEXT else "secondary"
        if st.button("Text", use_container_width=True, key="btn_text", type=btn_type):
            st.session_state.input_mode = InputMode.TEXT
            st.rerun()

    with ctrl2:
        btn_type = "primary" if st.session_state.input_mode == InputMode.VOICE else "secondary"
        if st.button("Voice", use_container_width=True, key="btn_voice", type=btn_type):
            st.session_state.input_mode = InputMode.VOICE
            st.rerun()

    with ctrl3:
        if st.button("Clear Chat", use_container_width=True, key="btn_clear"):
            SessionState.clear_chat()
            st.rerun()

    with ctrl4:
        if st.button("Export Chat", use_container_width=True, key="btn_export"):
            if st.session_state.chat_history:
                st.session_state.show_export = True
            else:
                st.toast("No messages to export", icon="W")

    if st.session_state.show_export:
        export_data = "\n\n".join([
            f"[{m.role.upper()}] {UI.format_timestamp(m.timestamp)}: {m.content or '[Audio]'}"
            for m in st.session_state.chat_history
        ])
        st.download_button(
            "Download Chat",
            export_data,
            file_name=f"voiceai_chat_{int(time.time())}.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_chat_btn"
        )


def render_voice_cloning_section():
    vc_title = "Voice Cloning - Active" if st.session_state.profile else "Voice Cloning - No Profile"
    with st.expander(vc_title, expanded=not st.session_state.profile):
        st.html("<h4>User Profile</h4>")
        uid_col, lang_col = st.columns([2, 1])

        with uid_col:
            new_uid = st.text_input(
                "User ID",
                value=st.session_state.user_id,
                placeholder="Enter unique user ID",
                help="Your voice profile is tied to this ID"
            )
            if new_uid != st.session_state.user_id:
                st.session_state.user_id = new_uid
                st.session_state.profile = VoiceProfileManager.load_profile(new_uid)
                st.rerun()

        with lang_col:
            new_lang = st.selectbox(
                "Language",
                options=list(SUPPORTED_LANGS.keys()),
                format_func=lambda x: SUPPORTED_LANGS[x],
                index=list(SUPPORTED_LANGS.keys()).index(st.session_state.lang)
            )
            if new_lang != st.session_state.lang:
                st.session_state.lang = new_lang

        st.html('<hr class="divider">')
        st.html("<h4>Voice Sample</h4>")

        audio_sample = st.audio_input(
            "Record a voice sample (5-30 seconds recommended)",
            key=f"enroll_{st.session_state.enroll_key}",
            label_visibility="collapsed"
        )

        if audio_sample:
            st.session_state.last_sample = audio_sample.getvalue()

        if st.session_state.last_sample:
            st.audio(st.session_state.last_sample, format="audio/wav")
            c1, c2, c3, c4 = st.columns([1, 1, 1, 2])

            with c1:
                if st.button("Replay", use_container_width=True, key="replay"):
                    st.toast("Playing sample...", icon="S")

            with c2:
                if st.button("Re-record", use_container_width=True, key="rerecord"):
                    st.session_state.last_sample = None
                    st.session_state.enroll_key += 1
                    st.rerun()

            with c3:
                if st.button("Clear", use_container_width=True, key="clear_sample"):
                    st.session_state.last_sample = None
                    st.rerun()

            with c4:
                if st.button("Enroll Voice", use_container_width=True, key="enroll_btn", type="primary"):
                    with st.spinner("Processing voice profile... This may take a moment"):
                        try:
                            data, sr = sf.read(io.BytesIO(st.session_state.last_sample))
                            st.session_state.profile = VoiceProfileManager.save_profile(
                                st.session_state.user_id, data, sr
                            )
                            st.success("Voice enrolled successfully.")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Enrollment failed: {str(e)}")

        if st.session_state.profile:
            st.html(
                f'<div class="badge" style="margin-top:12px; border: 1.5px solid var(--success)33; background: var(--success)10; color: var(--success);">'
                f'<span class="badge-dot" style="background:var(--success);"></span> '
                f'Profile active for {st.session_state.user_id}</div>'
            )
        else:
            st.html(
                '<div class="badge" style="margin-top:12px; border: 1.5px solid var(--warning)33; background: var(--warning)10; color: var(--warning);">'
                '<span class="badge-dot" style="background:var(--warning);"></span> '
                'Using default voice</div>'
            )


def main():
    st.set_page_config(
        page_title="VoiceAI",
        page_icon="V",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    SessionState.init()
    client = VoiceAIClient(API_URL)

    if time.time() - st.session_state.last_health_check > 30:
        st.session_state.api_status = client.health_check()
        st.session_state.last_health_check = time.time()

    st.html(THEME_CSS)

    UI.render_top_bar(
        st.session_state.user_id,
        st.session_state.input_mode,
        st.session_state.profile is not None,
        st.session_state.api_status
    )

    render_voice_cloning_section()
    st.html('<hr class="divider">')
    render_controls(client)
    UI.render_mode_badge(st.session_state.input_mode)
    st.html('<hr class="divider">')

    if not st.session_state.chat_history:
        UI.render_empty_state()
    else:
        for msg in st.session_state.chat_history:
            UI.render_chat_message(msg)

    if st.session_state.input_mode == InputMode.TEXT:
        handle_text_input(client)
    else:
        handle_voice_input(client)


if __name__ == "__main__":
    main()
