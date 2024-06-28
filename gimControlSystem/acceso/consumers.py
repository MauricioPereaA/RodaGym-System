# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class AccesoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("acceso_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("acceso_group", self.channel_name)

    async def enviar_datos_miembro(self, event):
        await self.send(text_data=json.dumps(event))
