import os
import io
import tempfile
from typing import Optional
import whisper
import numpy as np
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
import torch

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Whisper model
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
model = whisper.load_model(MODEL_SIZE).to(DEVICE)

print(f"Loaded Whisper model {MODEL_SIZE} on {DEVICE}")

def process_audio(audio_data: bytes, source_format: str = "webm") -> np.ndarray:
    """Convert audio data to format suitable for Whisper"""
    # Create a temporary file to save the audio
    with tempfile.NamedTemporaryFile(suffix=f".{source_format}") as temp_audio:
        temp_audio.write(audio_data)
        temp_audio.flush()
        
        # Load audio using pydub
        audio = AudioSegment.from_file(temp_audio.name, format=source_format)
        
        # Convert to WAV format if needed
        if source_format != "wav":
            with tempfile.NamedTemporaryFile(suffix=".wav") as temp_wav:
                audio.export(temp_wav.name, format="wav")
                audio = whisper.load_audio(temp_wav.name)
        else:
            audio = whisper.load_audio(temp_audio.name)
        
        return audio

@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile):
    """
    Transcribe audio file using Whisper
    Returns: {"text": transcribed_text, "confidence": confidence_score}
    """
    if not audio.filename.endswith((".wav", ".mp3", ".webm", ".m4a", ".ogg")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format. Supported formats: wav, mp3, webm, m4a, ogg"
        )
    
    try:
        # Read audio file
        audio_data = await audio.read()
        source_format = audio.filename.split(".")[-1]
        
        # Process audio to correct format
        audio_array = process_audio(audio_data, source_format)
        
        # Transcribe using Whisper
        result = model.transcribe(
            audio_array,
            language=None, #os.getenv("WHISPER_LANGUAGE", "zh"),
            task=os.getenv("WHISPER_TASK", "transcribe"),
            fp16=torch.cuda.is_available()
        )
        
        # Extract confidence scores if available
        confidence = 1.0
        if hasattr(result, "segments") and result.segments:
            # Average confidence across segments
            confidence = sum(seg.get("confidence", 1.0) for seg in result.segments) / len(result.segments)
        
        return {
            "text": result["text"].strip(),
            "confidence": float(confidence),
            "language": result["language"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9876) 