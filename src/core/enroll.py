import json
import numpy as np
import soundfile as sf
import librosa
from pathlib import Path

# Use /tmp on Streamlit Cloud — the working dir is read-only
import tempfile, os
DIR = Path(tempfile.gettempdir()) / "voice_profiles"
DIR.mkdir(exist_ok=True)


def save_voice_profile(uid: str, audio: np.ndarray, sr: int) -> dict:
    if audio.ndim > 1:
        audio = librosa.to_mono(audio.T)
    audio = librosa.resample(audio, orig_sr=sr, target_sr=22050)
    u_dir = DIR / uid
    u_dir.mkdir(parents=True, exist_ok=True)
    f_path = u_dir / "sample.wav"
    sf.write(str(f_path), audio, 22050)
    data = {"user_id": uid, "audio_path": str(f_path)}
    with open(u_dir / "profile.json", "w") as f:
        json.dump(data, f)
    return data


def load_voice_profile(uid: str):
    p = DIR / uid / "profile.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)