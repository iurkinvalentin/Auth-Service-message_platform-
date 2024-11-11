import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import GroupChat, Message
from .serializers import MessageSerializer

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket для группового чата."""

    async def connect(self):
        """Подключение к чату и добавление в группу."""
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.room_group_name = f"chat_{self.chat_id}"
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        logger.info("WebSocket подключен к чату %s", self.chat_id)
        await self.accept()

    async def disconnect(self, close_code):
        """Отключение от группы чата."""
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )
        logger.info(
            "WebSocket отключен от чата %s с кодом %s",
            self.chat_id,
            close_code,
        )

    async def receive(self, text_data):
        """Получение и обработка сообщения из WebSocket."""
        logger.info("Получено сообщение: %s", text_data)

        try:
            data = json.loads(text_data)
            message = data.get("message")

            if not await sync_to_async(
                lambda: self.scope["user"].is_authenticated
            )():
                logger.error("Пользователь не аутентифицирован.")
                await self.close()
                return

            user_id = self.scope["user"].id
            chat = await sync_to_async(GroupChat.objects.get)(id=self.chat_id)
            new_message = await sync_to_async(Message.objects.create)(
                content=message, sender_id=user_id, group_chat=chat
            )

            serialized_message = await sync_to_async(
                lambda: MessageSerializer(new_message).data
            )()
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_message", "message": serialized_message},
            )
        except Exception as e:
            logger.error("Ошибка обработки сообщения: %s", e)

    async def chat_message(self, event):
        """Отправка сообщения в WebSocket."""
        await self.send(text_data=json.dumps(event["message"]))


class PrivateChatConsumer(AsyncWebsocketConsumer):
    """WebSocket для приватного чата."""

    async def connect(self):
        """Подключение к приватной группе чата."""
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.room_group_name = f"private_chat_{self.chat_id}"
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """Отключение от приватной группы чата."""
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        """Получение и отправка сообщения в приватный чат."""
        data = json.loads(text_data)
        message = data["message"]
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", "message": message}
        )

    async def chat_message(self, event):
        """Отправка сообщения в WebSocket."""
        await self.send(text_data=json.dumps({"message": event["message"]}))
