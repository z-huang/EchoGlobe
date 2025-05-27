import os
import io
import tempfile
from typing import Optional
import whisper
import numpy as np
from fastapi import FastAPI, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
import torch
import json
import base64
from RealtimeSTT import AudioToTextRecorder

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

@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio transcription
    Expected message format: {
        "audio_data": "base64_encoded_audio_data",
        "format": "wav|mp3|webm|m4a|ogg"
    }
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive JSON data
            data = await websocket.receive_json()
            
            if not isinstance(data, dict) or "audio_data" not in data or "format" not in data:
                await websocket.send_json({
                    "error": "Invalid message format. Expected: {audio_data: string, format: string}"
                })
                continue
                
            # Decode base64 audio data
            try:
                audio_data = base64.b64decode(data["audio_data"])
            except Exception as e:
                await websocket.send_json({"error": f"Invalid base64 audio data: {str(e)}"})
                continue
                
            source_format = data["format"]
            if source_format is None: 
                source_format = "wav"
            if source_format not in ["wav", "mp3", "webm", "m4a", "ogg"]:
                await websocket.send_json({
                    "error": "Unsupported audio format. Supported formats: wav, mp3, webm, m4a, ogg"
                })
                continue
            
            try:
                # Process audio to correct format
                audio_array = process_audio(audio_data, source_format)
                
                # Transcribe using Whisper
                result = model.transcribe(
                    audio_array,
                    language=None,
                    task=os.getenv("WHISPER_TASK", "transcribe"),
                    fp16=torch.cuda.is_available()
                )
                
                # Calculate confidence
                confidence = 1.0
                if hasattr(result, "segments") and result.segments:
                    confidence = sum(seg.get("confidence", 1.0) for seg in result.segments) / len(result.segments)
                
                # Send back the result
                await websocket.send_json({
                    "text": result["text"].strip(),
                    "confidence": float(confidence),
                    "language": result["language"]
                })
                
            except Exception as e:
                await websocket.send_json({"error": str(e)})
                
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass

def convert_to_pcm(audio_data: bytes, source_format: str = "webm") -> bytes:
    """Convert audio data to PCM format"""
    with tempfile.NamedTemporaryFile(suffix=f".{source_format}") as temp_audio:
        temp_audio.write(audio_data)
        temp_audio.flush()
        
        # Load audio using pydub
        audio = AudioSegment.from_file(temp_audio.name, format=source_format)
        
        # Convert to PCM format
        pcm_data = io.BytesIO()
        # Export as WAV without header (raw PCM)
        audio.export(pcm_data, format="raw", codec="pcm_s16le", parameters=["-ar", "16000", "-ac", "1", "-f", "s16le"])
        return pcm_data.getvalue()

@app.websocket("/ws/stream_transcribe")
async def websocket_stream_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming transcription
    Expected message format: {
        "audio": "base64_encoded_audio_data",
        "format": "webm",
        "state": "start|stop"
    }
    Response format: {
        "text": "transcribed_text",
        "language": "detected_language",
        "status": "transcribing|done"
    }
    """
    await websocket.accept()
    
    recorder = AudioToTextRecorder(use_microphone=False, model="base")
    
    try:
        while True:
            # Receive JSON data
            data = await websocket.receive_json()
            
            if not isinstance(data, dict) or "audio" not in data or "format" not in data or "state" not in data:
                await websocket.send_json({
                    "error": "Invalid message format. Expected: {audio: string, format: string, state: string}"
                })
                continue
            
            state = data["state"]
            
            if state == "stop":
                # Send final transcription and cleanup
                final_text = recorder.text()
                await websocket.send_json({
                    "text": final_text,
                    "language": model.detect_language(final_text) if final_text else "unknown",
                    "status": "done"
                })
                recorder.shutdown()
                break
                
            # Decode base64 audio data
            try:
                audio_data = base64.b64decode(data["audio"])
            except Exception as e:
                await websocket.send_json({"error": f"Invalid base64 audio data: {str(e)}"})
                continue
            
            try:
                # Convert to PCM format
                pcm_data = convert_to_pcm(audio_data, data["format"])
                
                # Feed audio chunk to the recorder
                recorder.feed_audio(pcm_data)
                
                # Get current transcription
                current_text = recorder.text()
                
                # Send back the result
                await websocket.send_json({
                    "text": current_text,
                    "language": model.detect_language(current_text) if current_text else "unknown",
                    "status": "transcribing"
                })
                
            except Exception as e:
                await websocket.send_json({"error": str(e)})
                
    except WebSocketDisconnect:
        print("Client disconnected")
        recorder.shutdown()
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
        finally:
            recorder.shutdown()

if __name__ == "__main__":
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Whisper transcription server')
    parser.add_argument('--port', type=int, default=9876, help='Port to run the server on')
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port) 