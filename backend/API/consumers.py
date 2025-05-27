from channels.generic.websocket import AsyncWebsocketConsumer
import json
import websockets
import asyncio


class ProxyWebSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Example: ws://host/ws/transcribe/<conversation_id>/
        # Extract variable from self.scope['url_route']['kwargs']
        # conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        # You can now use conversation_id as needed
        self.target_url = 'ws://meow2.csie.ntu.edu.tw:9876/ws/stream_transcribe'
        if not self.target_url:
            await self.close()
            return

        self.target_ws = await websockets.connect(self.target_url)
        await self.accept()
        self.receive_task = asyncio.create_task(
            self.forward_from_target())

    async def disconnect(self, close_code):
        await self.target_ws.close()
        self.receive_task.cancel()

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is not None:
            await self.target_ws.send(text_data)
        elif bytes_data is not None:
            await self.target_ws.send(bytes_data)

    async def forward_from_target(self):
        try:
            async for message in self.target_ws:
                if isinstance(message, bytes):
                    await self.send(bytes_data=message)
                else:
                    await self.send(text_data=message)
        except Exception:
            await self.close()


class SimpleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({'a': 'hhh'}))

    async def disconnect(self, code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({
            'a': 'b'
        }))
