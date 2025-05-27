import os
import io
import tempfile
from typing import Optional
import whisper
import numpy as np
from fastapi import FastAPI, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import torch
import json
import base64
from RealtimeSTT import AudioToTextRecorder
import ffmpeg
import asyncio

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
        from pydub import AudioSegment
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
    """Convert audio data to PCM format using ffmpeg"""
    
    try:
        # Create input and output temp files
        with tempfile.NamedTemporaryFile(suffix=f".{source_format}", delete=False) as temp_in, \
             tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_out:
            
            # Write input audio
            temp_in.write(audio_data)
            temp_in.flush()
            in_filename = temp_in.name
            out_filename = temp_out.name
            
        
        try:
            # Use ffmpeg-python to convert to WAV
            
            # Convert directly to PCM using ffmpeg
            stream = ffmpeg.input(in_filename)
            stream = ffmpeg.output(stream, 'pipe:',
                               format='s16le',  # PCM signed 16-bit little-endian
                               acodec='pcm_s16le',
                               ac=1,  # mono
                               ar=16000)  # 16kHz
            
            # Run ffmpeg and capture output directly as bytes
            pcm_data, _ = ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
            
            return pcm_data
            
        except ffmpeg.Error as e:
            print("[DEBUG] FFmpeg error:")
            print(f"[DEBUG] stdout: {e.stdout.decode() if e.stdout else ''}")
            print(f"[DEBUG] stderr: {e.stderr.decode() if e.stderr else ''}")
            raise
        finally:
            # Clean up temp files
            try:
                os.unlink(in_filename)
                os.unlink(out_filename)
                print("[DEBUG] Cleaned up temporary files")
            except Exception as e:
                print(f"[DEBUG] Warning: Failed to clean up temporary files: {str(e)}")
                
    except Exception as e:
        print(f"[DEBUG] Error in conversion: {str(e)}")
        raise


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
    async def send_result(response: json):
        try:
            await websocket.send_json(response)
        except Exception as e: 
            await websocket.send_json({"error": str(e)})
        print("Message sent")

    def streaming_update(text: str):
        # Get current transcription
        print(f"Streaming update: {text}")
        asyncio.run(send_result({"text": text, "language": "en", "status": "update"}))

    def streaming_stablized(text: str):
        # Get current transcription
        print(f"Streaming stablized: {text}")
        asyncio.run(send_result({"text": text, "language": "en", "status": "stable"}))

    await websocket.accept()
    recorder = AudioToTextRecorder(
        use_microphone=False, model="base",
        enable_realtime_transcription=True,
        on_realtime_transcription_update=streaming_update,
        on_realtime_transcription_stabilized=streaming_stablized)
    recorder.start()
    
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
                recorder.shutdown()
                await websocket.send_json({
                    "text": None,
                    "language": "en",
                    "status": "done"
                })
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
                print("Successfully fed audio chunk to recorder")
                
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