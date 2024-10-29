from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, DatabaseError
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Chat, Message, ChatParticipant
from .serializers import ChatSerializer, MessageSerializer, PrivateChatSerializer
from accounts.models import CustomUser

CACHE_TIMEOUT = 300  # 5 минут


def handle_database_error(detail):
    """Обработчик ошибок базы данных"""
    return Response({"detail": detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def add_participant(chat, user_id, role='member'):
    """Добавление участника в чат с обработкой ошибок"""
    try:
        user = CustomUser.objects.get(id=user_id)
        ChatParticipant.objects.create(chat=chat, user=user, role=role)
        cache.delete(f"chat_participants_{chat.id}")  # Инвалидация кэша участников при добавлении нового
        return None
    except ObjectDoesNotExist:
        return Response({"detail": f"User with ID {user_id} not found."}, status=status.HTTP_404_NOT_FOUND)
    except IntegrityError:
        return Response({"detail": "Error adding participant to chat."}, status=status.HTTP_400_BAD_REQUEST)


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            chat = serializer.save()
            ChatParticipant.objects.create(chat=chat, user=request.user, role='admin')

            participants = request.data.get('participants', [])
            for user_id in participants:
                error_response = add_participant(chat, user_id)
                if error_response:
                    return error_response

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except DatabaseError:
            return handle_database_error("Database error occurred while creating chat.")

    def destroy(self, request, *args, **kwargs):
        chat = self.get_object()
        try:
            chat.participants.all().delete()
            chat.messages.all().delete()
            chat.delete()
            cache.delete(f"chat_{chat.id}")  # Удаление чата из кэша при удалении
            return Response({"detail": "Chat deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except DatabaseError:
            return handle_database_error("Database error occurred while deleting chat.")

    @action(detail=False, methods=['get'], url_path='my-chats')
    def list_my_chats(self, request):
        cache_key = f"user_chats_{request.user.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            chats = Chat.objects.filter(participants__user=request.user).distinct()
            serializer = self.get_serializer(chats, many=True)
            cache.set(cache_key, serializer.data, timeout=CACHE_TIMEOUT)  # Кэшируем результат
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DatabaseError:
            return handle_database_error("Database error occurred while fetching chats.")

    @action(detail=True, methods=['post'], url_path='add-participant')
    def add_participant(self, request, pk=None):
        """Добавление пользователя в групповой чат администратором"""
        chat = self.get_object()

        # Проверка, что текущий пользователь является администратором
        if not ChatParticipant.objects.filter(chat=chat, user=request.user, role='admin').exists():
            return Response({"detail": "You do not have permission to add participants to this chat."}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Добавление участника в чат
        error_response = add_participant(chat, user_id)
        if error_response:
            return error_response

        return Response({"detail": "Participant successfully added to chat."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='remove-participant')
    def remove_participant(self, request, pk=None):
        """Удаление пользователя в групповой чат администратором"""
        chat = self.get_object()
        creator_participant = ChatParticipant.objects.filter(chat=chat, user=request.user, role='admin').first()

        if not creator_participant:
            return Response({"detail": "You do not have permission to remove participants from this chat."}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            participant = ChatParticipant.objects.get(chat=chat, user__id=user_id)
            participant.delete()
            cache.delete(f"chat_participants_{chat.id}")  # Инвалидация кэша участников чата
            return Response({"detail": "Participant successfully removed from chat."}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"detail": "Participant not found in this chat."}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError:
            return handle_database_error("Database error occurred while removing participant.")



class PrivateChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.filter(group=None)
    serializer_class = PrivateChatSerializer

    def create(self, request, *args, **kwargs):
        """Создание нового личного чата с равными правами для обоих участников"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        participants = request.data.get('participants')
        try:
            chat = Chat.objects.create()
            for user_id in participants:
                error_response = add_participant(chat, user_id, role='admin')
                if error_response:
                    return error_response
            return Response(ChatSerializer(chat).data, status=status.HTTP_201_CREATED)
        except DatabaseError:
            return handle_database_error("Database error occurred while creating private chat.")


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def perform_create(self, serializer):
        """Указываем отправителя при создании сообщения"""
        try:
            serializer.save(sender=self.request.user)
        except DatabaseError:
            return handle_database_error("Database error occurred while saving message.")
