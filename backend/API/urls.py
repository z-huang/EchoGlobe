from django.urls import path
from .views import llama_chatbot

urlpatterns = [
    path('llama_chatbot/', llama_chatbot, name='llama_chatbot'),
]