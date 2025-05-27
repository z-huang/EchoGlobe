from django.urls import path, re_path
from .views import *

urlpatterns = [
    path('llama_chatbot/', llama_chatbot, name='llama_chatbot'),
    path('translate/', translate_view),
    path('transcribe_file/', proxy_file_upload),
    path('conversation/<int:conversation_id>/', get_conversation_sentences),
]
