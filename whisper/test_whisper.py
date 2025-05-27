import asyncio
import websockets
import json
import base64
import argparse
from pathlib import Path
from pydub import AudioSegment
import io
import time
import aiohttp

async def test_stream_transcribe(file_path, server_url, window_ms=2000):
    """
    Test the streaming transcription with audio chunks of specified window size
    Args:
        file_path: Path to the audio file
        server_url: WebSocket server URL
        window_ms: Window size in milliseconds (default: 2000ms)
    """
    # Ensure URL has protocol for WebSocket
    if not server_url.startswith(('ws://', 'wss://')):
        server_url = f"ws://{server_url}/ws/stream_transcribe"

    async def send_chunks(websocket, chunks):
        """Send all audio chunks"""
        for i, chunk in enumerate(chunks):
            # Export chunk to bytes
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
            print(f"Sent chunk {i + 1}/{len(chunks)}")
            
            # Add a small delay to allow receive task to process responses
            await asyncio.sleep(0.1)
            
        # Send stop signal
        print("\nSending stop signal...")
        await websocket.send(json.dumps({
            "audio": "",
            "format": "webm",
            "state": "stop"
        }))

    async def receive_responses(websocket):
        """Receive and print responses until done"""
        while True:
            try:
                # Use a short timeout to check for messages frequently
                result = json.loads(await asyncio.wait_for(websocket.recv(), timeout=0.05))
                print(f"Received result: {result}")
                
                if "error" in result:
                    print(f"Error: {result['error']}")
                    return result
                    
                print(f"\nStatus: {result['status']}")
                if result['text']:
                    print(f"Text: {result['text']}")
                    
                if result['status'] == "done":
                    return result
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error receiving response: {str(e)}")
                return {"error": str(e)}

    async with websockets.connect(server_url) as websocket:
        # Load audio file
        audio = AudioSegment.from_file(file_path)
        
        chunks = [
            audio[i:i + window_ms]
            for i in range(0, len(audio), window_ms)
        ]
        
        # Create tasks for sending and receiving
        send_task = asyncio.create_task(send_chunks(websocket, chunks))
        receive_task = asyncio.create_task(receive_responses(websocket))
        
        # Wait for both tasks to complete
        await asyncio.gather(send_task, receive_task)
        
        # Return the result from receive task
        return receive_task.result()

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

async def test_transcribe(file_path: str, server_url: str = "http://localhost:9876"):
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
    
    # Ensure URL has protocol
    if not server_url.startswith(('http://', 'https://')):
        server_url = f"http://{server_url}"
    
    try:
        # Open and send the file
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('audio',
                             f,
                             filename=Path(file_path).name,
                             content_type=f'audio/{file_format}')
                
                print(f"Sending file to {server_url}/transcribe...")
                async with session.post(f"{server_url}/transcribe", data=data) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    print("\nTranscription Result:")
                    print("-" * 50)
                    print(f"Text: {result['text']}")
                    print(f"English: {result['english']}")
                    print(f"Chinese: {result['chinese']}")
                    print(f"Japanese: {result['japanese']}")
                    print(f"German: {result['german']}")
                    
    except aiohttp.ClientError as e:
        print(f"Error making request: {e}")
        print(f"Full URL attempted: {server_url}/transcribe")
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
        result = asyncio.run(test_transcribe(args.file, args.url))    