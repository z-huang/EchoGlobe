import requests
import argparse
from pathlib import Path

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
    parser.add_argument("--url", default="http://localhost:9000",
                      help="Whisper service URL (default: http://localhost:9000)")
    
    args = parser.parse_args()
    test_transcribe(args.file, args.url) 