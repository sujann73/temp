from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/your-endpoint/', consumers.MyConsumer.as_asgi()),
]
