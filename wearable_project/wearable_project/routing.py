# wearable_project/routing.py
from django.urls import re_path
from videostream.consumers import VideoStreamConsumer

websocket_urlpatterns = [
    re_path(r"^ws/videostream/$", VideoStreamConsumer.as_asgi()),  # Basic videostream
    re_path(r"^ws/stream/$", VideoStreamConsumer.as_asgi()),  # Surgical workflow stream
]