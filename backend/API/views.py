from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

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
            'Authorization': 'Bearer sk-d63d4c1d8d29403caef217b601bc9b25',  # Replace with your actual token
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
            model_answer = chatbot_response.get("choices", [{}])[0].get("message", {}).get("content", "")
            return JsonResponse({"answer": model_answer})
        else:
            return Response({"error": "Failed to fetch response from chatbot API"}, status=response.status_code)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)