# notifications/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Временно закомментируем проверку аутентификации для тестирования
        # self.user = self.scope['user']
        # if self.user.is_authenticated:
        #     self.group_name = f"notifications_{self.user.id}"
        #     await self.channel_layer.group_add(self.group_name, self.channel_name)
        #     await self.accept()
        # else:
        #     await self.close()

        # Примите соединение без проверки
        await self.accept()

    async def disconnect(self, close_code):
        # Здесь также можно закомментировать удаление пользователя из группы, так как мы временно не используем группу
        # if self.user.is_authenticated:
        #     await self.channel_layer.group_discard(self.group_name, self.channel_name)
        pass

    async def receive(self, text_data):
        pass  # WebSocket не получает данные от клиента, только отправляет

    async def send_notification(self, event):
        notification = event['message']
        await self.send(text_data=json.dumps({'message': notification}))
