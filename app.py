import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from datetime import datetime

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
    timestamp: float = field(default_factory=time.time)
    error: bool = False

    def to_api_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class TextAIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "X-Client": "textai-streamlit/1.0"
        })

    def health_check(self) -> bool:
        try:
            resp = self.session.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def send_text(
        self, history: List[Dict], lang: str, user_id: str
    ) -> Tuple[Optional[str], Optional[str]]:
        try:
            resp = self.session.post(
                f"{self.base_url}/text",
                json={"history": history, "lang": lang, "user_id": user_id},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get("reply") or data.get("text") or data.get("response")
            return text, None
        except requests.exceptions.Timeout:
            return None, "Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            return None, "Cannot connect to server. Please check your connection."
        except Exception as e:
            return None, f"Error: {str(e)}"


class SessionState:
    @staticmethod
    def init():
        defaults = {
            "chat_history": [],
            "user_id": "default_user",
            "lang": "ar",
            "api_status": False,
            "last_health_check": 0,
        }
        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

    @staticmethod
    def clear_chat():
        st.session_state.chat_history = []

    @staticmethod
    def add_message(msg: ChatMessage):
        st.session_state.chat_history.append(msg)
        if len(st.session_state.chat_history) > MAX_HISTORY * 2:
            st.session_state.chat_history = st.session_state.chat_history[-MAX_HISTORY * 2:]


THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700&display=swap');

html, body, .stApp {
    background: #0d0f14 !important;
    font-family: 'Syne', sans-serif;
}

section[data-testid="stSidebar"] {
    background: #111318 !important;
    border-right: 1px solid #1e2030;
}

.top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 0 1.2rem;
    border-bottom: 1px solid #1e2030;
    margin-bottom: 1rem;
}
.top-bar h2 {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 700;
    color: #e8eaf0;
    letter-spacing: -0.02em;
}
.top-bar small {
    color: #555a72;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
}
.status-pill {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    padding: 4px 10px;
    border-radius: 100px;
    background: #1a1d28;
    border: 1px solid #2a2d3e;
    color: #888da8;
}
.status-pill.online { color: #4ade80; border-color: #14532d; background: #0a1a0f; }

.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #3a3d52;
}
.empty-state h3 { font-size: 1.1rem; font-weight: 600; color: #4a4d62; margin-bottom: 0.5rem; }
.empty-state p { font-size: 0.85rem; font-family: 'DM Mono', monospace; }

div[data-testid="stChatMessage"] {
    background: transparent !important;
}
div[data-testid="stChatMessage"] > div:last-child {
    background: #13151e !important;
    border: 1px solid #1e2030 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    color: #c8cad8 !important;
    font-size: 0.9rem !important;
    font-family: 'Syne', sans-serif !important;
}

.stTextInput input, .stSelectbox select, div[data-baseweb="select"] {
    background: #13151e !important;
    border-color: #1e2030 !important;
    color: #c8cad8 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.85rem !important;
    border-radius: 8px !important;
}

div[data-testid="stChatInput"] textarea {
    background: #13151e !important;
    border: 1px solid #1e2030 !important;
    color: #c8cad8 !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
}

.stButton > button {
    background: #13151e !important;
    border: 1px solid #1e2030 !important;
    color: #888da8 !important;
    border-radius: 8px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    border-color: #3a3d52 !important;
    color: #c8cad8 !important;
    background: #1a1d28 !important;
}

.stExpander {
    background: #13151e !important;
    border: 1px solid #1e2030 !important;
    border-radius: 10px !important;
}

.stDivider { border-color: #1e2030 !important; }
</style>
"""


def render_top_bar(user_id: str, api_online: bool):
    status_class = "online" if api_online else ""
    status_text = "● online" if api_online else "● offline"
    st.markdown(f"""
    <div class="top-bar">
        <div>
            <h2>TextAI Chat</h2>
            <small>user: {user_id}</small>
        </div>
        <span class="status-pill {status_class}">{status_text}</span>
    </div>
    """, unsafe_allow_html=True)


def render_empty_state():
    st.markdown("""
    <div class="empty-state">
        <h3>No messages yet</h3>
        <p>Type below to start a conversation.</p>
    </div>
    """, unsafe_allow_html=True)


def render_chat_message(msg: ChatMessage):
    with st.chat_message(msg.role):
        st.markdown(msg.content)
        if msg.error:
            st.caption("⚠ Error generating response")


def handle_text_input(client: TextAIClient):
    prompt = st.chat_input("Message...")
    if prompt and prompt.strip():
        user_msg = ChatMessage(role="user", content=prompt.strip())
        SessionState.add_message(user_msg)

        history = [m.to_api_dict() for m in st.session_state.chat_history[-MAX_HISTORY:]]

        with st.spinner("Generating response..."):
            text_response, error = client.send_text(
                history, st.session_state.lang, st.session_state.user_id
            )

        if error:
            assistant_msg = ChatMessage(role="assistant", content=error, error=True)
        elif text_response:
            assistant_msg = ChatMessage(role="assistant", content=text_response)
        else:
            assistant_msg = ChatMessage(role="assistant", content="No response received.", error=True)

        SessionState.add_message(assistant_msg)
        st.rerun()


def render_sidebar():
    with st.sidebar:
        st.markdown("### Settings")
        st.divider()

        new_uid = st.text_input("User ID", value=st.session_state.user_id)
        if new_uid != st.session_state.user_id:
            st.session_state.user_id = new_uid
            st.rerun()

        lang_options = list(SUPPORTED_LANGS.keys())
        lang_labels = list(SUPPORTED_LANGS.values())
        current_idx = lang_options.index(st.session_state.lang) if st.session_state.lang in lang_options else 0
        selected_label = st.selectbox("Language", lang_labels, index=current_idx)
        selected_lang = lang_options[lang_labels.index(selected_label)]
        if selected_lang != st.session_state.lang:
            st.session_state.lang = selected_lang
            st.rerun()

        st.divider()

        msg_count = len(st.session_state.chat_history)
        st.caption(f"Messages: {msg_count}")

        if st.button("🗑 Clear Chat", use_container_width=True):
            SessionState.clear_chat()
            st.rerun()


def main():
    st.set_page_config(page_title="TextAI Chat", page_icon="💬", layout="wide")
    SessionState.init()
    client = TextAIClient(API_URL)

    st.markdown(THEME_CSS, unsafe_allow_html=True)

    # Health check (every 60s)
    now = time.time()
    if now - st.session_state.last_health_check > 60:
        st.session_state.api_status = client.health_check()
        st.session_state.last_health_check = now

    render_sidebar()
    render_top_bar(st.session_state.user_id, st.session_state.api_status)

    # Chat display
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            render_chat_message(msg)
    else:
        render_empty_state()

    handle_text_input(client)


if __name__ == "__main__":
    main()
