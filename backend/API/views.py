from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
import websockets
from rest_framework.parsers import MultiPartParser, FormParser
from Conversation.models import *


@api_view(['POST'])
def translate_view(request):
    try:
        text = request.data.get("text", "")
        if not text:
            return Response({"error": "Text is required"}, status=status.HTTP_400_BAD_REQUEST)

        def translate_to(target_lang):
            url = 'https://cts.m3.ntu.edu.tw/api/chat/completions'
            headers = {
                'Authorization': 'Bearer sk-d63d4c1d8d29403caef217b601bc9b25',
                'Content-Type': 'application/json'
            }
            system_prompt = f"You are a translator. Translate the following text to {target_lang}. If they are the same language, return the original text. Do not output any other words."
            data = {
                "model": "llama3.1:8B",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ]
            }
            try:
                resp = requests.post(url, headers=headers, json=data)
                if resp.status_code == 200:
                    return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                return f"API error: {resp.status_code}"
            except Exception as e:
                return f"Exception: {str(e)}"

        translations = {
            "en": translate_to("English"),
            "cn": translate_to("Traditional Chinese"),
            "de": translate_to("German"),
            "jp": translate_to("Japanese"),
        }
        return Response(translations, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Only allow logged-in users
def llama_chatbot(request):
    try:
        # Extract conversation history and user message from the request
        payload = request.data
        conversation_history = payload.get('conversation_history', [])
        user_message = payload.get('message')

        if not user_message:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Add a system prompt as the first message in the conversation history
        if not any(msg.get("role") == "system" for msg in conversation_history):
            conversation_history.insert(0, {
                "role": "system",
                "content": "You are a helpful assistant that answers user's questions."
            })
        # Ensure the conversation history is a list of dictionaries with 'role' and 'content'
        if not isinstance(conversation_history, list):
            return Response({"error": "Conversation history must be a list"}, status=status.HTTP_400_BAD_REQUEST)
        # Forward the conversation to the external chatbot API
        url = 'https://cts.m3.ntu.edu.tw/api/chat/completions'
        headers = {
            # Replace with your actual token
            'Authorization': 'Bearer sk-d63d4c1d8d29403caef217b601bc9b25',
            'Content-Type': 'application/json'
        }
        data = {
            "model": "llama3.1:8B",
            "messages": conversation_history
        }
        response = requests.post(url, headers=headers, json=data)

        # Check if the external API call was successful
        if response.status_code == 200:
            chatbot_response = response.json()
            # Extract and return only the model's answer
            model_answer = chatbot_response.get("choices", [{}])[
                0].get("message", {}).get("content", "")
            return JsonResponse({"answer": model_answer})
        else:
            return Response({"error": "Failed to fetch response from chatbot API"}, status=response.status_code)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProxyWebSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.target_url = 'http://meow1.csie.ntu.edu.tw:9876/ws/transcribe'
        if not self.target_url:
            await self.close()
            return

        self.target_ws = await websockets.connect(self.target_url)
        await self.accept()
        self.receive_task = self.channel_layer.loop.create_task(
            self.forward_from_target())

    async def disconnect(self, close_code):
        await self.target_ws.close()
        self.receive_task.cancel()

    async def receive(self, text_data=None, bytes_data=None):
        if hasattr(self, 'target_ws'):
            if text_data is not None:
                await self.target_ws.send(text_data)
            elif bytes_data is not None:
                await self.target_ws.send(bytes_data)

    async def forward_from_target(self):
        try:
            async for message in self.target_ws:
                if isinstance(message, bytes):
                    await self.send(bytes_data=message)
                else:
                    await self.send(text_data=message)
        except Exception:
            await self.close()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def proxy_file_upload(request):
    # Ensure the request uses the correct parsers
    parser_classes = (MultiPartParser, FormParser)
    file_obj = request.FILES.get('audio')
    conversation_id = request.data.get('conversation_id')
    if conversation_id is None:
        return Response({"error": "No conversation id provided"}, status=status.HTTP_400_BAD_REQUEST)

    if not file_obj:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    files = {'audio': (file_obj.name, file_obj, file_obj.content_type)}

    target_url = 'http://meow1.csie.ntu.edu.tw:9876/transcribe'
    try:
        resp = requests.post(target_url, files=files)
        try:
            data = resp.json()
        except Exception as json_err:
            return Response({"error": "Invalid JSON response from target"}, status=status.HTTP_502_BAD_GATEWAY)

        # Insert sentences into database
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            for sentence in data:
                Sentence.objects.create(
                    conversation=conversation,
                    source_transcription=sentence['source_transcription'],
                    en_transcription=sentence['en_transcription'],
                    cn_transcription=sentence['cn_transcription'],
                    de_transcription=sentence['de_transcription'],
                    jp_transcription=sentence['jp_transcription'],
                )
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as db_err:
            return Response({"error": f"Database error: {str(db_err)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(data, status=resp.status_code)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
