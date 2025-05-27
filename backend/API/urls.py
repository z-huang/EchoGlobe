from django.urls import path, re_path
from .views import llama_chatbot, proxy_file_upload, ProxyWebSocketConsumer

urlpatterns = [
    path('llama_chatbot/', llama_chatbot, name='llama_chatbot'),
    re_path(r'ws/transcript/$', ProxyWebSocketConsumer.as_asgi()),
    path('transcribe_file/', proxy_file_upload)
]