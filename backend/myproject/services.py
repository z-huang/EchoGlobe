import requests
from django.conf import settings
from typing import Tuple, List, Optional
import json



class LLMService:
    def __init__(self):
        self.base_url = settings.LLM_SERVER_URL

    def translate_text(self, text: str, target_lang: str) -> str:
        """Translate text to target language using LLM service"""
        try:
            response = requests.post(
                f"{self.base_url}/translate",
                json={"text": text, "target_lang": target_lang}
            )
            response.raise_for_status()
            return response.json()["text"]
        except requests.RequestException as e:
            print(f"Translation error: {e}")
            return text  # Return original text on error

    def merge_text(self, prev_text: str, new_text: str, confidence: float) -> str:
        """Merge two text segments using LLM service"""
        try:
            response = requests.post(
                f"{self.base_url}/merge_text",
                json={
                    "prev_text": prev_text,
                    "new_text": new_text,
                    "confidence": confidence
                }
            )
            response.raise_for_status()
            return response.json()["merged_text"]
        except requests.RequestException as e:
            print(f"Text merge error: {e}")
            # Fallback to simple concatenation if LLM service fails
            return f"{prev_text} {new_text}" if prev_text else new_text

    def chat(self, meeting_contents: List[dict], prompt: str) -> str:
        """Generate chat response based on meeting contents"""
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "contents": meeting_contents,
                    "prompt": prompt
                }
            )
            response.raise_for_status()
            return response.json()["result"]
        except requests.RequestException as e:
            print(f"Chat error: {e}")
            return "Sorry, I couldn't process your request at this time."


class WhisperService:
    def __init__(self):
        self.base_url = settings.WHISPER_SERVER_URL

    async def transcribe(self, audio_data: bytes) -> Tuple[str, float]:
        """
        Transcribe audio data using Whisper service
        Returns: (transcribed_text, confidence_score)
        """
        try:
            files = {'audio': ('audio.webm', audio_data, 'audio/webm')}
            response = requests.post(
                f"{self.base_url}/transcribe",
                files=files
            )
            response.raise_for_status()
            result = response.json()
            return result["text"], result.get("confidence", 1.0)
        except requests.RequestException as e:
            print(f"Transcription error: {e}")
            return "", -1
