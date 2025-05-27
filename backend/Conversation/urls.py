from django.urls import path
from . import views

urlpatterns = [
    path('new_conversation/', views.new_conversation, name='new_conversation'),
    path('<slug:slug>/', views.single_chat, name='handle_slug'),
]