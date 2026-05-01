import asyncio
import functools
import tempfile
from pathlib import Path
import torch
from TTS.api import TTS


_tts = None


def _get_tts():
    global _tts
    if _tts is None:
        _tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        _tts.to("cuda" if torch.cuda.is_available() else "cpu")
    return _tts


def _synthesize_sync(text: str, lang: str, speaker_wav: str | None):
    tts = _get_tts()

    out_file = Path(tempfile.gettempdir()) / "xtts_out.wav"

    tts.tts_to_file(
        text=text,
        speaker_wav=speaker_wav if speaker_wav and Path(speaker_wav).exists() else None,
        language=lang if lang else "ar",
        file_path=str(out_file),
    )

    return out_file.read_bytes()


async def synthesize_to_bytes(
    text: str,
    lang: str = "ar",
    speaker_wav: str | None = None,
):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        functools.partial(_synthesize_sync, text, lang, speaker_wav),
    )