import asyncio
import websockets
import json
import base64
import argparse
from pathlib import Path
from pydub import AudioSegment
import io
import time

async def test_stream_transcribe(file_path, server_url, window_ms=2000):
    """
    Test the streaming transcription with audio chunks of specified window size
    Args:
        file_path: Path to the audio file
        server_url: WebSocket server URL
        window_ms: Window size in milliseconds (default: 2000ms)
    """
    async with websockets.connect(f'ws://{server_url}/ws/stream_transcribe') as websocket:
        # Load audio file
        audio = AudioSegment.from_file(file_path)
        
        # Calculate chunk size in milliseconds
        chunk_duration = window_ms  # 2000ms = 2s
        
        # Process audio in chunks
        for i in range(0, len(audio), chunk_duration):
            # Extract chunk
            chunk = audio[i:i + chunk_duration]
            
            # Export chunk to bytes (as webm)
            chunk_data = io.BytesIO()
            chunk.export(chunk_data, format='webm')
            chunk_bytes = chunk_data.getvalue()
            
            # Encode chunk
            audio_data = base64.b64encode(chunk_bytes).decode('utf-8')
            
            # Send chunk
            await websocket.send(json.dumps({
                "audio": audio_data,
                "format": "webm",
                "state": "start"
            }))
            
            # Get and print intermediate result
            result = json.loads(await websocket.recv())
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print("\nIntermediate Result:")
                print(f"Text: {result['text']}")
                print(f"Status: {result['status']}")
                print(f"Language: {result['language']}")
            
            # Simulate real-time processing by waiting
            await asyncio.sleep(chunk_duration / 1000)  # Convert ms to seconds
        
        # Send stop signal
        await websocket.send(json.dumps({
            "audio": "",
            "format": "webm",
            "state": "stop"
        }))
        
        # Get final result
        final_result = json.loads(await websocket.recv())
        return final_result

async def test_transcribe_socket(file_path, server_url):
    """Legacy function for non-streaming transcription"""
    async with websockets.connect(f'ws://{server_url}/ws/transcribe') as websocket:
        # Read and encode audio file
        with open(file_path, 'rb') as f:
            audio_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Send audio data
        await websocket.send(json.dumps({
            "audio_data": audio_data,
            "format": file_path.split('.')[-1]  # Get format from file extension
        }))
        
        # Get and print result
        result = json.loads(await websocket.recv())
        return result

def test_transcribe(file_path: str, server_url: str = "http://localhost:9000"):
    """Test the Whisper transcription service with an audio file"""
    
    # Check if file exists
    if not Path(file_path).exists():
        print(f"Error: File {file_path} does not exist")
        return
    
    # Get the file format
    file_format = Path(file_path).suffix.lower()[1:]  # Remove the dot
    if file_format not in ['wav', 'mp3', 'webm', 'm4a', 'ogg']:
        print(f"Error: Unsupported format {file_format}. Supported formats: wav, mp3, webm, m4a, ogg")
        return
    
    try:
        # Open and send the file
        with open(file_path, 'rb') as f:
            files = {'audio': (Path(file_path).name, f, f'audio/{file_format}')}
            print(f"Sending file to {server_url}/transcribe...")
            
            response = requests.post(f"{server_url}/transcribe", files=files)
            response.raise_for_status()
            
            result = response.json()
            print("\nTranscription Result:")
            print("-" * 50)
            print(f"Text: {result['text']}")
            print(f"Confidence: {result['confidence']:.2f}")
            
    except requests.RequestException as e:
        print(f"Error making request: {e}")
        if hasattr(e.response, 'text'):
            print(f"Server response: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Whisper transcription service")
    parser.add_argument("file", help="Path to the audio file to transcribe")
    parser.add_argument("--url", default="localhost:9876",
                      help="Whisper service URL (default: localhost:9876)")
    parser.add_argument("--stream", action="store_true",
                      help="Use streaming transcription")
    parser.add_argument("--window", type=int, default=2000,
                      help="Window size in milliseconds for streaming (default: 2000)")
    
    args = parser.parse_args()
    
    # Run the appropriate async function with asyncio.run()
    if args.stream:
        print(f"Testing streaming transcription with {args.window}ms windows...")
        result = asyncio.run(test_stream_transcribe(args.file, args.url, args.window))
    else:
        print("Testing regular transcription...")
        result = asyncio.run(test_transcribe_socket(args.file, args.url))
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("\nFinal Result:")
        print("-" * 50)
        print(f"Text: {result['text']}")
        if 'confidence' in result:
            print(f"Confidence: {result['confidence']:.2f}")
        print(f"Language: {result['language']}")
        if 'status' in result:
            print(f"Status: {result['status']}") 