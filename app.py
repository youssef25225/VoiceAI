```python
import io
import streamlit as st
import soundfile as sf
import requests
from src.core.enroll import save_voice_profile, load_voice_profile

API_URL = "https://yousefemam-voiceai.hf.space"

st.set_page_config(
    page_title="VoiceAI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap');

:root {
    --bg: #080a0f;
    --surface: #0e1117;
    --surface2: #141820;
    --surface3: #1a1f2e;
    --border: #1e2435;
    --border-lt: #2a3148;
    --accent: #4f7cff;
    --accent2: #7c9fff;
    --accent-dim: rgba(79,124,255,.08);
    --accent-glow: rgba(79,124,255,.20);
    --muted: #4a5568;
    --text: #e8ecf4;
    --text-dim: #8892a4;
    --green: #2dd4a0;
    --amber: #f5a623;
    --radius: 14px;
    --radius-sm: 9px;
    --shadow: 0 2px 12px rgba(0,0,0,.4);
}

@media (prefers-color-scheme: light) {
    :root {
        --bg: #f4f6fb;
        --surface: #ffffff;
        --surface2: #f0f2f8;
        --surface3: #e8ecf5;
        --border: #dde1ee;
        --border-lt: #c8cfe0;
        --accent: #3a6aef;
        --accent2: #2a56d6;
        --accent-dim: rgba(58,106,239,.07);
        --accent-glow: rgba(58,106,239,.18);
        --muted: #8a94a8;
        --text: #111827;
        --text-dim: #4b5563;
        --green: #0e9e6e;
        --amber: #c47d0a;
        --shadow: 0 2px 12px rgba(0,0,0,.08);
    }
}

* { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Geist', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
    padding: 2.5rem 3rem 6rem !important;
    max-width: 820px !important;
    margin: 0 auto !important;
}

[data-testid="stSidebar"] { display: none !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: var(--border-lt); border-radius: 99px; }

.top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 2rem;
    margin-bottom: 2rem;
    border-bottom: 1px solid var(--border);
}

.brand { display: flex; gap: 12px; align-items: center; }

.brand-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: linear-gradient(135deg, var(--accent), #7c9fff);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 24px var(--accent-glow);
}

.brand-name {
    font-family: 'Instrument Serif', serif !important;
    font-size: 1.55rem;
}

.status-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.76rem;
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 7px 15px;
    border-radius: 99px;
}

.status-dot { width: 7px; height: 7px; background: var(--green); border-radius: 50%; }

[data-testid="stChatMessage"] { background: transparent !important; }

.stChatMessage > div:last-child {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 14px 16px !important;
    max-width: 78% !important;
    color: var(--text) !important;
    box-shadow: var(--shadow) !important;
}

.stChatMessage p, .stChatMessage span, .stChatMessage div { color: var(--text) !important; }

[data-testid="stChatMessageContent"] * { color: var(--text) !important; }

div[data-testid="stChatMessage"]:has(svg[data-testid="chatAvatarIcon-user"]) .stChatMessage > div:last-child {
    background: var(--surface3) !important;
    border-color: var(--border-lt) !important;
}

[data-testid="stChatInput"] textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border-lt) !important;
    color: var(--text) !important;
    border-radius: var(--radius) !important;
}

[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

.stButton > button {
    background: var(--surface2) !important;
    border: 1px solid var(--border-lt) !important;
    color: var(--text-dim) !important;
    border-radius: var(--radius-sm) !important;
}

.stButton > button:hover {
    background: var(--accent) !important;
    color: white !important;
    transform: translateY(-1px);
}

audio { width: 100% !important; border-radius: var(--radius-sm) !important; }

.voice-banner {
    background: var(--accent-dim);
    border: 1px solid rgba(79,124,255,.2);
    padding: 12px 16px;
    border-radius: var(--radius);
    color: var(--accent2);
}

.divider { border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

if "chat"        not in st.session_state: st.session_state.chat = []
if "user_id"     not in st.session_state: st.session_state.user_id = "default_user"
if "profile"     not in st.session_state: st.session_state.profile = load_voice_profile(st.session_state.user_id)
if "input_mode"  not in st.session_state: st.session_state.input_mode = "text"
if "audio_key"   not in st.session_state: st.session_state.audio_key = 0
if "enroll_key"  not in st.session_state: st.session_state.enroll_key = 0
if "last_sample" not in st.session_state: st.session_state.last_sample = None

st.markdown(f"""
<div class="top-bar">
    <div class="brand">
        <div class="brand-icon">🎙️</div>
        <div>
            <div class="brand-name">VoiceAI</div>
            <div class="brand-sub">Intelligent Voice Assistant</div>
        </div>
    </div>
    <div class="status-pill">
        <span class="status-dot"></span>
        {st.session_state.user_id}
        &nbsp;·&nbsp;
        {st.session_state.input_mode.title()} Mode
        &nbsp;·&nbsp;
        {"Voice Cloned" if st.session_state.profile else "Default Voice"}
    </div>
</div>
""", unsafe_allow_html=True)

vc_title = "Voice Cloning — Active" if st.session_state.profile else "Voice Cloning — No profile"
with st.expander(vc_title, expanded=not st.session_state.profile):
    st.markdown('<div class="section-label">User Profile</div>', unsafe_allow_html=True)
    uid_col, _ = st.columns([1, 2])
    with uid_col:
        uid = st.text_input("User ID", value=st.session_state.user_id, placeholder="Enter user ID")
        if uid != st.session_state.user_id:
            st.session_state.user_id = uid
            st.session_state.profile = load_voice_profile(uid)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Voice Sample</div>', unsafe_allow_html=True)

    _v = st.audio_input("Record sample", key=f"enroll_{st.session_state.enroll_key}", label_visibility="collapsed")
    if _v:
        st.session_state.last_sample = _v.getvalue()

    if st.session_state.last_sample:
        st.audio(st.session_state.last_sample, format="audio/wav")
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("Replay", use_container_width=True, key="replay"):
                st.toast("Playing sample", icon="🔊")
        with c2:
            if st.button("Re-record", use_container_width=True, key="rerecord"):
                st.session_state.last_sample = None
                st.session_state.enroll_key += 1
                st.rerun()
        with c3:
            if st.button("Enroll Voice", use_container_width=True, key="enroll_btn"):
                with st.spinner("Processing voice profile..."):
                    _data, _sr = sf.read(io.BytesIO(st.session_state.last_sample))
                    st.session_state.profile = save_voice_profile(uid, _data, _sr)
                st.success("Voice enrolled successfully.")
                st.rerun()

    if st.session_state.profile:
        st.markdown(f'<div class="badge badge-green" style="margin-top:8px;"><span class="badge-dot"></span> Profile active for {uid}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge badge-amber" style="margin-top:8px;"><span class="badge-dot"></span> Using default voice</div>', unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

c1, c2, c3, _ = st.columns([1, 1, 1, 2])
with c1:
    if st.button("Text Mode", use_container_width=True, key="btn_text"):
        st.session_state.input_mode = "text"
        st.rerun()
with c2:
    if st.button("Voice Mode", use_container_width=True, key="btn_voice"):
        st.session_state.input_mode = "voice"
        st.rerun()
with c3:
    if st.button("Clear Chat", use_container_width=True, key="btn_clear"):
        st.session_state.chat = []
        st.rerun()

mode_color = "#4f7cff" if st.session_state.input_mode == "text" else "#7c9fff"
st.markdown(f"""
<div class="badge badge-blue" style="margin-top:10px;border-color:{mode_color}33;background:{mode_color}10;color:{mode_color};">
    <span class="badge-dot" style="background:{mode_color};box-shadow:0 0 5px {mode_color};"></span>
    {st.session_state.input_mode.title()} Mode Active
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

if not st.session_state.chat:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">💬</div>
        <div class="empty-title">Start a conversation</div>
        <div class="empty-sub">Type a message or switch to Voice Mode to speak with the assistant.</div>
    </div>""", unsafe_allow_html=True)
else:
    for m in st.session_state.chat:
        if m.get("audio"):
            with st.chat_message(m["role"]):
                st.audio(m["audio"], format="audio/wav")

if st.session_state.input_mode == "text":
    prompt = st.chat_input("Message VoiceAI...")
    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                try:
                    res = requests.post(
                        f"{API_URL}/text",
                        json={
                            "history": [
                                {"role": m["role"], "content": m.get("content", "")}
                                for m in st.session_state.chat[-10:]
                            ],
                            "lang": "ar",
                            "user_id": st.session_state.user_id,
                        },
                        timeout=600
                    )
                    res.raise_for_status()
                    data = res.json()
                    audio_hex   = data.get("audio")
                    audio_bytes = bytes.fromhex(audio_hex) if audio_hex else None
                except Exception as e:
                    st.error(f"API error: {e}")
                    audio_bytes = None

            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")

        st.session_state.chat.append({"role": "assistant", "audio": audio_bytes})
        st.rerun()

else:
    st.markdown('<div class="voice-banner">Voice Mode — Record your message then press Send</div>', unsafe_allow_html=True)
    audio_msg = st.audio_input("Record", key=f"voice_{st.session_state.audio_key}", label_visibility="collapsed")
    if audio_msg:
        col_send, _ = st.columns([1, 3])
        with col_send:
            send = st.button("Send Voice", use_container_width=True)
        if send:
            with st.spinner("Transcribing and generating response..."):
                try:
                    files = {"file": ("audio.wav", audio_msg.getvalue(), "audio/wav")}
                    res = requests.post(
                        f"{API_URL}/voice",
                        files=files,
                        params={"user_id": st.session_state.user_id},
                        timeout=600
                    )
                    res.raise_for_status()
                    data = res.json()
                    if "error" in data:
                        st.error(data["error"])
                        st.stop()
                    audio_hex   = data.get("audio")
                    audio_bytes = bytes.fromhex(audio_hex) if audio_hex else None
                except Exception as e:
                    st.error(f"API error: {e}")
                    st.stop()

            if audio_bytes:
                st.session_state.chat.append({"role": "user",      "audio": None})
                st.session_state.chat.append({"role": "assistant", "audio": audio_bytes})
                st.session_state.audio_key += 1
                st.rerun()
            else:
                st.warning("No audio received. Please try again.")
```
