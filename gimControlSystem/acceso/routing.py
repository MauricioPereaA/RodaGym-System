from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    path('ws/acceso/', consumers.AccesoConsumer.as_asgi()),
]