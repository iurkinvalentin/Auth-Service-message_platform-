import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import GroupChat, Message
from .serializers import MessageSerializer
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        
        # Подключение к комнате
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info("WebSocket connected to chat %s", self.chat_id)
        await self.accept()

    async def disconnect(self, close_code):
        # Отключение от комнаты
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info("WebSocket disconnected from chat %s with close code %s", self.chat_id, close_code)

    async def receive(self, text_data):
        logger.info("Received message: %s", text_data)
        
        try:
            data = json.loads(text_data)
            message = data.get('message')
            
            # Проверяем, что пользователь аутентифицирован
            if self.scope['user'].is_authenticated:
                user_id = self.scope['user'].id
            else:
                logger.error("User is not authenticated.")
                return

            # Выполняем синхронные запросы к базе данных через sync_to_async
            chat = await sync_to_async(GroupChat.objects.get)(id=self.chat_id)
            new_message = await sync_to_async(Message.objects.create)(
                content=message,
                sender_id=user_id,
                group_chat=chat
            )

            # Асинхронная сериализация нового сообщения
            serialized_message = await self.serialize_message(new_message)

            # Отправка сообщения всем пользователям в комнате
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': serialized_message
                }
            )
        except Exception as e:
            logger.error("Error processing message: %s", e)

    async def chat_message(self, event):
        # Отправка сообщения через WebSocket
        await self.send(text_data=json.dumps(event['message']))

    @sync_to_async
    def serialize_message(self, message):
        """Сериализация сообщения в асинхронном контексте."""
        return MessageSerializer(message).data

