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
    initial_sidebar_state="expanded"
)

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

:root {
    --bg:        #0a0b0f;
    --surface:   #111318;
    --surface2:  #1a1c24;
    --border:    #242630;
    --accent:    #5b6ef5;
    --accent2:   #9d7ff7;
    --muted:     #6b7280;
    --text:      #e8eaf0;
    --text-dim:  #9ca3af;
    --green:     #34d399;
    --amber:     #fbbf24;
    --red:       #f87171;
    --radius:    14px;
    --radius-sm: 8px;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem !important; max-width: 100% !important; }
section[data-testid="stSidebar"] > div { padding-top: 1.5rem !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* ── Top header ── */
.vai-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 2rem;
}
.vai-logo {
    width: 44px; height: 44px;
    border-radius: var(--radius-sm);
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
}
.vai-title {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    margin: 0 !important;
    background: linear-gradient(90deg, #e8eaf0 60%, var(--accent2));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.vai-meta {
    font-size: 0.72rem;
    color: var(--muted);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 1px;
}

/* ── Sidebar label ── */
.sb-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 6px;
}
.sb-divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.4rem 0;
}

/* ── Status badges ── */
.badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px; border-radius: 99px;
    font-size: 0.76rem; font-weight: 500;
}
.badge-green  { background: rgba(52,211,153,.12); color: var(--green); border:1px solid rgba(52,211,153,.25); }
.badge-amber  { background: rgba(251,191,36,.1);  color: var(--amber); border:1px solid rgba(251,191,36,.2); }
.badge-blue   { background: rgba(91,110,245,.12); color: var(--accent); border:1px solid rgba(91,110,245,.25); }
.badge-dot    { width:6px; height:6px; border-radius:50%; background:currentColor; }

/* ── Mode pills ── */
.mode-pill {
    display: inline-flex; gap: 4px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 99px; padding: 3px;
    margin-bottom: 0.5rem;
}
.mode-pill span {
    padding: 5px 14px; border-radius: 99px;
    font-size: 0.78rem; font-weight: 500; cursor: pointer;
    transition: all .2s;
}
.mode-active {
    background: var(--accent) !important;
    color: #fff !important;
}
.mode-inactive { color: var(--muted) !important; }

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 4px 0 !important;
}

/* User bubble */
[data-testid="stChatMessage"][data-testid*="user"],
div[class*="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    flex-direction: row-reverse !important;
}

/* Streamlit chat bubbles override */
.stChatMessage > div:last-child {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 12px 16px !important;
    font-size: 0.92rem !important;
    line-height: 1.6 !important;
    max-width: 75% !important;
}

/* ── Input area ── */
[data-testid="stChatInput"] textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(91,110,245,.15) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 8px 16px !important;
    transition: all .18s !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #fff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(91,110,245,.3) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* Primary CTA */
.stButton.primary > button,
button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
    border: none !important;
    color: #fff !important;
}

/* ── Text inputs ── */
[data-testid="stTextInput"] input {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(91,110,245,.15) !important;
}

/* ── Audio recorder ── */
[data-testid="stAudioInput"] {
    background: var(--surface2) !important;
    border: 1px dashed var(--border) !important;
    border-radius: var(--radius) !important;
}

/* ── Info / warning boxes ── */
[data-testid="stAlert"] {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.82rem !important;
}

/* ── Sidebar section headers ── */
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-family: 'Syne', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--muted) !important;
    margin-bottom: 10px !important;
}

/* ── Audio player ── */
audio {
    border-radius: var(--radius-sm) !important;
    height: 36px !important;
    width: 100% !important;
    filter: invert(0.9) hue-rotate(190deg) !important;
}

/* ── Empty state ── */
.empty-state {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 12px; padding: 80px 20px;
    color: var(--muted); text-align: center;
}
.empty-icon {
    font-size: 3rem; opacity: .4;
}
.empty-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem; font-weight: 600;
    color: var(--text-dim);
}
.empty-sub { font-size: 0.85rem; max-width: 300px; line-height: 1.6; }

/* ── Waveform animation ── */
@keyframes wave {
    0%, 100% { transform: scaleY(0.4); }
    50%       { transform: scaleY(1); }
}
.waveform {
    display: flex; align-items: center; gap: 3px; height: 20px;
}
.waveform span {
    display: block; width: 3px; background: var(--accent);
    border-radius: 99px; animation: wave 1s ease-in-out infinite;
}
.waveform span:nth-child(1){ animation-delay:0s;    height:8px; }
.waveform span:nth-child(2){ animation-delay:.1s;   height:14px; }
.waveform span:nth-child(3){ animation-delay:.2s;   height:20px; }
.waveform span:nth-child(4){ animation-delay:.3s;   height:14px; }
.waveform span:nth-child(5){ animation-delay:.4s;   height:8px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────
if "chat"          not in st.session_state: st.session_state.chat = []
if "user_id"       not in st.session_state: st.session_state.user_id = "default_user"
if "profile"       not in st.session_state: st.session_state.profile = load_voice_profile(st.session_state.user_id)
if "input_mode"    not in st.session_state: st.session_state.input_mode = "text"
if "audio_key"     not in st.session_state: st.session_state.audio_key = 0
if "enroll_key"    not in st.session_state: st.session_state.enroll_key = 0
if "last_sample"   not in st.session_state: st.session_state.last_sample = None

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo + app name
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:1.5rem;">
        <div style="width:36px;height:36px;border-radius:8px;background:linear-gradient(135deg,#5b6ef5,#9d7ff7);
                    display:flex;align-items:center;justify-content:center;font-size:18px;">🎙️</div>
        <div>
            <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;
                        background:linear-gradient(90deg,#e8eaf0,#9d7ff7);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                VoiceAI
            </div>
            <div style="font-size:0.65rem;color:#6b7280;letter-spacing:.08em;text-transform:uppercase;">
                Voice Assistant
            </div>
        </div>
    </div>
    <hr style="border:none;border-top:1px solid #242630;margin-bottom:1.2rem;">
    """, unsafe_allow_html=True)

    # User ID
    st.markdown('<div class="sb-label">User ID</div>', unsafe_allow_html=True)
    uid = st.text_input("User ID", value=st.session_state.user_id, label_visibility="collapsed", placeholder="Enter user ID…")
    if uid != st.session_state.user_id:
        st.session_state.user_id = uid
        st.session_state.profile = load_voice_profile(uid)

    st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

    # Voice cloning section
    st.markdown('<div class="sb-label">🎤 Voice Cloning</div>', unsafe_allow_html=True)

    v_in = st.audio_input(
        "Record a sample (5–15 sec)",
        key=f"enroll_audio_{st.session_state.enroll_key}",
        label_visibility="collapsed",
    )

    # Persist the latest recording across reruns
    if v_in:
        st.session_state.last_sample = v_in.getvalue()

    # Show player + action buttons whenever we have a sample
    if st.session_state.last_sample:
        st.audio(st.session_state.last_sample, format="audio/wav")

        col_replay, col_rerecord = st.columns(2)
        with col_replay:
            # Replay = just re-render the audio player (already above); give
            # the button a visual cue via a toast notification.
            if st.button("▶ Replay", use_container_width=True, key="btn_replay"):
                st.toast("Playing sample…", icon="🔊")
        with col_rerecord:
            if st.button("↺ Re-record", use_container_width=True, key="btn_rerecord"):
                st.session_state.last_sample = None
                st.session_state.enroll_key += 1   # forces a fresh audio_input widget
                st.rerun()

    if st.session_state.last_sample and st.button("✦ Enroll Voice", use_container_width=True):
        with st.spinner("Processing voice profile…"):
            data_arr, sr = sf.read(io.BytesIO(st.session_state.last_sample))
            st.session_state.profile = save_voice_profile(uid, data_arr, sr)
        st.success("Voice enrolled successfully!")

    if st.session_state.profile:
        st.markdown(f"""
        <div class="badge badge-green" style="margin-top:8px;width:100%;justify-content:center;">
            <span class="badge-dot"></span> Profile active · {uid}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="badge badge-amber" style="margin-top:8px;width:100%;justify-content:center;">
            <span class="badge-dot"></span> Using default voice
        </div>""", unsafe_allow_html=True)

    st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

    # Input mode
    st.markdown('<div class="sb-label">Input Mode</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        text_active = "primary" if st.session_state.input_mode == "text" else ""
        if st.button("⌨️  Text", use_container_width=True, key="btn_text"):
            st.session_state.input_mode = "text"
            st.rerun()
    with col2:
        if st.button("🎙️  Voice", use_container_width=True, key="btn_voice"):
            st.session_state.input_mode = "voice"
            st.rerun()

    # Active mode indicator
    mode_color = "#5b6ef5" if st.session_state.input_mode == "text" else "#9d7ff7"
    st.markdown(f"""
    <div class="badge badge-blue" style="width:100%;justify-content:center;margin-top:4px;
         border-color:{mode_color}33;background:{mode_color}18;color:{mode_color};">
        <span class="badge-dot" style="background:{mode_color};"></span>
        {st.session_state.input_mode.title()} Mode Active
    </div>""", unsafe_allow_html=True)

    st.markdown('<hr class="sb-divider">', unsafe_allow_html=True)

    if st.button("🗑  Clear conversation", use_container_width=True):
        st.session_state.chat = []
        st.rerun()

    # Bottom meta
    st.markdown("""
    <div style="position:fixed;bottom:1.5rem;left:1rem;right:1rem;font-size:0.7rem;color:#4b5563;text-align:center;">
        VoiceAI · Powered by XTTS v2
    </div>""", unsafe_allow_html=True)

# ── Main area ──────────────────────────────────────────────────────────────

# Header
st.markdown(f"""
<div class="vai-header">
    <div class="vai-logo">🎙️</div>
    <div>
        <div class="vai-title">VoiceAI</div>
        <div class="vai-meta">
            {st.session_state.input_mode.title()} Mode &nbsp;·&nbsp; {st.session_state.user_id}
            &nbsp;·&nbsp; {"Voice cloned" if st.session_state.profile else "Default voice"}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Voice Cloning panel (always visible in main area) ─────────────────────
_vc_label = "🎤 Voice Cloning — Profile active ✓" if st.session_state.profile else "🎤 Voice Cloning — No profile yet"
with st.expander(_vc_label, expanded=not st.session_state.profile):
    st.markdown(
        "<p style='font-size:.82rem;color:#9ca3af;margin:0 0 10px'>Record 5–15 seconds of your voice, then press <strong style='color:#e8eaf0'>Enroll</strong>.</p>",
        unsafe_allow_html=True,
    )

    _uid = st.session_state.user_id

    _v = st.audio_input(
        "Record sample",
        key=f"main_enroll_{st.session_state.enroll_key}",
        label_visibility="collapsed",
    )
    if _v:
        st.session_state.last_sample = _v.getvalue()

    if st.session_state.last_sample:
        st.audio(st.session_state.last_sample, format="audio/wav")

        _c1, _c2, _c3 = st.columns([1, 1, 2])
        with _c1:
            if st.button("▶ Replay", use_container_width=True, key="main_replay"):
                st.toast("Playing sample…", icon="🔊")
        with _c2:
            if st.button("↺ Re-record", use_container_width=True, key="main_rerecord"):
                st.session_state.last_sample = None
                st.session_state.enroll_key += 1
                st.rerun()
        with _c3:
            if st.button("✦ Enroll Voice", use_container_width=True, key="main_enroll_btn"):
                with st.spinner("Processing voice profile…"):
                    import io as _io
                    _data, _sr = sf.read(_io.BytesIO(st.session_state.last_sample))
                    st.session_state.profile = save_voice_profile(_uid, _data, _sr)
                st.success("Voice enrolled! The assistant will now clone your voice.")
                st.rerun()

    if st.session_state.profile:
        st.markdown(f"""
        <div class="badge badge-green" style="margin-top:6px;">
            <span class="badge-dot"></span> Profile active for <strong>{_uid}</strong>
        </div>""", unsafe_allow_html=True)

# Chat messages or empty state
if not st.session_state.chat:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">💬</div>
        <div class="empty-title">Start a conversation</div>
        <div class="empty-sub">Type a message below or switch to Voice Mode to speak directly to the assistant.</div>
    </div>""", unsafe_allow_html=True)
else:
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.write(m["content"])
            if m.get("audio"):
                st.audio(m["audio"], format="audio/wav")

# ── Text mode ──────────────────────────────────────────────────────────────
if st.session_state.input_mode == "text":
    prompt = st.chat_input("Message VoiceAI…")

    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("⏳ Generating response… (CPU mode — may take 30–90 sec)"):
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
                    reply = f"⚠️ API error: {e}"
                    audio_bytes = None

        st.session_state.chat.append({
            "role": "assistant",
            "content": reply,
            "audio": audio_bytes
        })
        st.rerun()

# ── Voice mode ─────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style="background:rgba(91,110,245,.07);border:1px solid rgba(91,110,245,.2);
                border-radius:12px;padding:14px 18px;font-size:0.84rem;color:#9ca3af;margin-bottom:1rem;">
        🎙️ <strong style="color:#e8eaf0;">Voice Mode</strong> — Record your message then press <strong style="color:#e8eaf0;">Send</strong>
    </div>""", unsafe_allow_html=True)

    audio_msg = st.audio_input("Record", key=f"voice_input_{st.session_state.audio_key}", label_visibility="collapsed")

    if audio_msg:
        col_send, col_discard = st.columns([1, 3])
        with col_send:
            send = st.button("▶  Send Voice", use_container_width=True)
        if send:
            with st.spinner("⏳ Transcribing & generating… (CPU mode — may take 30–90 sec):"):
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

                    user_text  = data.get("text", "")
                    reply      = data.get("reply", "")
                    audio_hex  = data.get("audio")
                    audio_bytes = bytes.fromhex(audio_hex) if audio_hex else None

                except Exception as e:
                    st.error(f"⚠️ API error: {e}")
                    st.stop()

            if user_text:
                st.session_state.chat.append({"role": "user",      "content": user_text})
                st.session_state.chat.append({"role": "assistant", "content": reply, "audio": audio_bytes})
                st.session_state.audio_key += 1
                st.rerun()
            else:
                st.warning("No speech detected — please try again.")
