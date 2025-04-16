from django.urls import path
from . import views

urlpatterns = [
    path('api/login/',        views.api_login,        name='api_login'),
    path('api/transactions/', views.api_transactions, name='api_transactions'),
    path('api/roommates/',    views.api_roommates,    name='api_roommates'),
]
