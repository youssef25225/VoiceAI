import os
os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN", "")
import traceback
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import io
import soundfile as sf
from src.core.asr import transcribe
from src.core.llm import generate_full
from src.core.tts import synthesize_to_bytes
from src.core.enroll import load_voice_profile

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    history: list[dict]
    lang: str = "ar"
    user_id: str = "default_user"
    
@app.get("/")
def root():
    return {"status": "VoiceAssistant running"}

@app.post("/text")
async def process_text(request: TextRequest):
    try:
        reply = generate_full(request.history)
        profile = load_voice_profile(request.user_id)
        speaker_wav = profile.get("audio_path") if profile else None

        audio_out = await synthesize_to_bytes(reply, request.lang, speaker_wav)
        return {
            "reply": reply,
            "audio": audio_out.hex()
        }
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/voice")
async def process_voice(file: UploadFile = File(...), user_id: str = "default_user"):
    try:
        audio_bytes = await file.read()
        data, sr = sf.read(io.BytesIO(audio_bytes))
        result = transcribe(data, sr)
        text = result["text"]
        lang = result.get("language", "ar")
        reply = generate_full([{"role": "user", "content": text}])
        profile = load_voice_profile(user_id)
        speaker_wav = profile.get("audio_path") if profile else None

        audio_out = await synthesize_to_bytes(reply, lang, speaker_wav)
        return {
            "text": text,
            "reply": reply,
            "audio": audio_out.hex()
        }
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
