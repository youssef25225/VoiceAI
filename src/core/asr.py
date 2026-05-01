import torch
import numpy as np
import whisper
import librosa
from functools import lru_cache

@lru_cache(maxsize=1)
def load_whisper():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return whisper.load_model("tiny", device=device)

def transcribe(audio: np.ndarray, sr: int) -> dict:
    model = load_whisper()
    if sr != 16000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
    if audio.ndim > 1:
        audio = librosa.to_mono(audio.T)
    result = model.transcribe(audio.astype(np.float32))
    return {
        "text": result["text"].strip(),
        "language": result.get("language", "en"),
    }
