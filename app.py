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
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Instrument+Serif:ital@0;1&display=swap');

:root {
    --bg:         #f8faff;
    --surface:    #ffffff;
    --surface2:   #f0f4ff;
    --border:     #e2e8f7;
    --accent:     #1d4ed8;
    --accent-lt:  #3b82f6;
    --accent-bg:  #eff6ff;
    --muted:      #94a3b8;
    --text:       #0f172a;
    --text-dim:   #475569;
    --green:      #059669;
    --green-bg:   #ecfdf5;
    --amber:      #d97706;
    --amber-bg:   #fffbeb;
    --radius:     16px;
    --radius-sm:  10px;
    --shadow:     0 1px 3px rgba(15,23,42,.06), 0 4px 16px rgba(15,23,42,.04);
    --shadow-md:  0 4px 24px rgba(29,78,216,.10);
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem 5rem !important; max-width: 860px !important; margin: 0 auto !important; }
[data-testid="stSidebar"] { display: none !important; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }

.vai-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}
.vai-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}
.vai-icon {
    width: 42px; height: 42px;
    background: var(--accent);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: var(--shadow-md);
}
.vai-name {
    font-family: 'Instrument Serif', serif !important;
    font-size: 1.5rem;
    font-weight: 400;
    color: var(--accent);
    letter-spacing: -0.01em;
}
.vai-sub {
    font-size: 0.72rem;
    color: var(--muted);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-weight: 500;
}
.vai-status {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.78rem;
    color: var(--text-dim);
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 6px 14px;
    border-radius: 99px;
    box-shadow: var(--shadow);
}
.vai-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 0 2px var(--green-bg);
}

.section-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: var(--shadow);
}
.section-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 1rem;
}

.badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px; border-radius: 99px;
    font-size: 0.76rem; font-weight: 600;
}
.badge-green { background: var(--green-bg); color: var(--green); border: 1px solid #a7f3d0; }
.badge-amber { background: var(--amber-bg); color: var(--amber); border: 1px solid #fde68a; }
.badge-blue  { background: var(--accent-bg); color: var(--accent); border: 1px solid #bfdbfe; }
.badge-dot   { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 6px 0 !important;
}
.stChatMessage > div:last-child {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 14px 18px !important;
    font-size: 0.93rem !important;
    line-height: 1.65 !important;
    max-width: 78% !important;
    box-shadow: var(--shadow) !important;
    color: var(--text) !important;
}
div[class*="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stChatMessage > div:last-child {
    background: var(--accent-bg) !important;
    border-color: #bfdbfe !important;
}

[data-testid="stChatInput"] textarea {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.93rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent-lt) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,.12) !important;
}

.stButton > button {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text-dim) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
    transition: all .18s !important;
}
.stButton > button:hover {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #fff !important;
    box-shadow: var(--shadow-md) !important;
    transform: translateY(-1px) !important;
}

[data-testid="stTextInput"] input {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.88rem !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--accent-lt) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,.12) !important;
}

[data-testid="stAudioInput"] {
    background: var(--accent-bg) !important;
    border: 1.5px dashed #bfdbfe !important;
    border-radius: var(--radius) !important;
}

[data-testid="stAlert"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.83rem !important;
    color: var(--text-dim) !important;
}

audio {
    border-radius: var(--radius-sm) !important;
    height: 36px !important;
    width: 100% !important;
}

.empty-state {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 10px; padding: 70px 20px;
    text-align: center;
}
.empty-icon { font-size: 2.8rem; opacity: .25; }
.empty-title {
    font-family: 'Instrument Serif', serif;
    font-size: 1.2rem;
    color: var(--text-dim);
}
.empty-sub { font-size: 0.84rem; color: var(--muted); max-width: 280px; line-height: 1.6; }

.divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.2rem 0;
}

.mode-bar {
    display: flex;
    gap: 8px;
    align-items: center;
}
</style>
""", unsafe_allow_html=True)

if "chat"        not in st.session_state: st.session_state.chat = []
if "user_id"     not in st.session_state: st.session_state.user_id = "default_user"
if "profile"     not in st.session_state: st.session_state.profile = load_voice_profile(st.session_state.user_id)
if "input_mode"  not in st.session_state: st.session_state.input_mode = "text"
if "audio_key"   not in st.session_state: st.session_state.audio_key = 0
if "enroll_key"  not in st.session_state: st.session_state.enroll_key = 0
if "last_sample" not in st.session_state: st.session_state.last_sample = None

profile_label = "Voice Cloned" if st.session_state.profile else "Default Voice"
mode_label    = st.session_state.input_mode.title() + " Mode"

st.markdown(f"""
<div class="vai-top">
    <div class="vai-brand">
        <div class="vai-icon">🎙️</div>
        <div>
            <div class="vai-name">VoiceAI</div>
            <div class="vai-sub">Intelligent Voice Assistant</div>
        </div>
    </div>
    <div class="vai-status">
        <span class="vai-dot"></span>
        {st.session_state.user_id} &nbsp;·&nbsp; {mode_label} &nbsp;·&nbsp; {profile_label}
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("Voice Cloning" + (" — Active" if st.session_state.profile else ""), expanded=not st.session_state.profile):
    st.markdown('<div class="section-title">Enroll your voice</div>', unsafe_allow_html=True)

    uid_col, _ = st.columns([1, 2])
    with uid_col:
        uid = st.text_input("User ID", value=st.session_state.user_id, placeholder="Enter user ID")
        if uid != st.session_state.user_id:
            st.session_state.user_id = uid
            st.session_state.profile = load_voice_profile(uid)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

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
        st.markdown(f'<div class="badge badge-green"><span class="badge-dot"></span> Profile active for {uid}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge badge-amber"><span class="badge-dot"></span> Using default voice</div>', unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

m_col1, m_col2, m_col3 = st.columns([1, 1, 4])
with m_col1:
    if st.button("Text Mode", use_container_width=True, key="btn_text"):
        st.session_state.input_mode = "text"
        st.rerun()
with m_col2:
    if st.button("Voice Mode", use_container_width=True, key="btn_voice"):
        st.session_state.input_mode = "voice"
        st.rerun()
with m_col3:
    if st.button("Clear conversation", use_container_width=True, key="btn_clear"):
        st.session_state.chat = []
        st.rerun()

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
        with st.chat_message(m["role"]):
            st.write(m["content"])
            if m.get("audio"):
                st.audio(m["audio"], format="audio/wav")

if st.session_state.input_mode == "text":
    prompt = st.chat_input("Message VoiceAI...")

    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                try:
                    res = requests.post(
                        f"{API_URL}/text",
                        json={
                            "history": [
                                {"role": m["role"], "content": m["content"]}
                                for m in st.session_state.chat[-10:]
                            ],
                            "lang": "ar",
                            "user_id": st.session_state.user_id,
                        },
                        timeout=600
                    )
                    res.raise_for_status()
                    data = res.json()
                    reply = data.get("reply", "")
                    audio_hex = data.get("audio")
                    audio_bytes = bytes.fromhex(audio_hex) if audio_hex else None
                except Exception as e:
                    reply = f"API error: {e}"
                    audio_bytes = None

        st.session_state.chat.append({"role": "assistant", "content": reply, "audio": audio_bytes})
        st.rerun()

else:
    st.markdown("""
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;
                padding:12px 16px;font-size:0.84rem;color:#1d4ed8;margin-bottom:1rem;font-weight:500;">
        Voice Mode — Record your message then press Send
    </div>""", unsafe_allow_html=True)

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

                    user_text   = data.get("text", "")
                    reply       = data.get("reply", "")
                    audio_hex   = data.get("audio")
                    audio_bytes = bytes.fromhex(audio_hex) if audio_hex else None

                except Exception as e:
                    st.error(f"API error: {e}")
                    st.stop()

            if user_text:
                st.session_state.chat.append({"role": "user", "content": user_text})
                st.session_state.chat.append({"role": "assistant", "content": reply, "audio": audio_bytes})
                st.session_state.audio_key += 1
                st.rerun()
            else:
                st.warning("No speech detected. Please try again.")
