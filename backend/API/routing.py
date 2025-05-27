from django.urls import path, re_path
from .consumers import *

websocket_urlpatterns = [
    # re_path(r'ws/transcript/(?P<conversation_id>\w+)/$', ProxyWebSocketConsumer.as_asgi()),
    path('ws/transcript/', ProxyWebSocketConsumer.as_asgi()),
    re_path(r'ws/test/$', SimpleConsumer.as_asgi()),
]
