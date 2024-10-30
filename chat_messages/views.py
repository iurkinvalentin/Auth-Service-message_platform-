from django.core.cache import cache
from django.db import IntegrityError, DatabaseError
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import GroupChat, Message, ChatParticipant, PrivateChat
from .serializers import GroupChatSerializer, MessageSerializer, PrivateChatSerializer
from accounts.models import CustomUser

CACHE_TIMEOUT = 250  # 5 минут

def handle_database_error(detail):
    """Обработчик ошибок базы данных"""
    return Response({"detail": detail}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def update_chat_cache(chat):
    """Обновление кэша участников для конкретного чата"""
    cache_key = f"chat_participants_{chat.id}"
    updated_participants = list(ChatParticipant.objects.filter(chat=chat).values("user__username", "role"))
    cache.set(cache_key, updated_participants, timeout=CACHE_TIMEOUT)
    print("Кэш обновлен с новыми данными:", cache.get(cache_key))


def add_participant(chat, user_id, role='member'):
    """Добавление участника в чат с проверкой на существование и инвалидацией кэша"""
    try:
        user = CustomUser.objects.get(id=user_id)
        if ChatParticipant.objects.filter(chat=chat, user=user).exists():
            return Response({"detail": "User is already a participant in this chat."}, status=status.HTTP_400_BAD_REQUEST)
        
        ChatParticipant.objects.create(chat=chat, user=user, role=role)
        cache.delete(f"user_chats_{user_id}")  # Инвалидация кэша списка чатов пользователя
        cache.delete(f"chat_participants_{chat.id}")  # Инвалидация кэша участников чата
        update_chat_cache(chat)  # Обновление кэша чата
        return None
    except CustomUser.DoesNotExist:
        return Response({"detail": f"User with ID {user_id} not found."}, status=status.HTTP_404_NOT_FOUND)
    except IntegrityError:
        return Response({"detail": "Error adding participant to chat."}, status=status.HTTP_400_BAD_REQUEST)


class GroupChatViewSet(viewsets.ModelViewSet):
    queryset = GroupChat.objects.all()
    serializer_class = GroupChatSerializer

    def create(self, request, *args, **kwargs):
        """Создание нового чата и добавление админа и участников"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Получаем участников, включая создателя
        participants = request.data.get('participants', [])
        participants_ids = set(participants + [request.user.id])

        # Проверка на существование чата с аналогичными участниками
        existing_chats = GroupChat.objects.filter(
            participants__user_id__in=participants_ids
        ).distinct()

        for chat in existing_chats:
            chat_participant_ids = set(chat.participants.values_list('user_id', flat=True))
            if chat_participant_ids == participants_ids:
                return Response(
                    {"detail": "A chat with the same participants already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            # Создаем новый чат
            chat = serializer.save()
            ChatParticipant.objects.create(chat=chat, user=request.user, role='admin')

            # Добавляем участников
            for user_id in participants:
                error_response = add_participant(chat, user_id)
                if error_response:
                    return error_response

            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except DatabaseError:
            return handle_database_error("Database error occurred while creating chat.")

    def destroy(self, request, *args, **kwargs):
        """Удаление чата вместе с его участниками и сообщениями"""
        chat = self.get_object()
        try:
            participant_ids = chat.participants.values_list('user_id', flat=True)
            chat.participants.all().delete()  # Удаление всех участников
            chat.messages.all().delete()      # Удаление всех сообщений
            chat.delete()

            for user_id in participant_ids:
                cache.delete(f"user_chats_{user_id}")

            cache.delete(f"chat_{chat.id}")
            cache.delete(f"chat_participants_{chat.id}") # Удаление чата из кэша при удалении
            return Response({"detail": "Chat deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except DatabaseError as e:
            # Обработка исключения базы данных с подробным сообщением об ошибке
            return handle_database_error(f"Database error occurred while deleting chat: {str(e)}")

    @action(detail=False, methods=['get'], url_path='my-all-chats')
    def list_all_user_chats(self, request):
        """Получить список всех чатов пользователя (групповых и приватных)"""
        user = request.user
        cache_key = f"all_chats_{user.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        try:
            # Получаем групповые чаты, в которых пользователь является участником
            group_chats = GroupChat.objects.filter(participants__user=user).distinct()
            group_chats_data = GroupChatSerializer(group_chats, many=True).data

            # Получаем приватные чаты, где пользователь является одним из участников
            private_chats = PrivateChat.objects.filter(user1=user) | PrivateChat.objects.filter(user2=user)
            private_chats = private_chats.distinct()
            private_chats_data = PrivateChatSerializer(private_chats, many=True).data

            # Комбинируем данные обоих типов чатов
            all_chats_data = {
                "group_chats": group_chats_data,
                "private_chats": private_chats_data
            }

            # Кэшируем результат
            cache.set(cache_key, all_chats_data, timeout=CACHE_TIMEOUT)
            return Response(all_chats_data, status=status.HTTP_200_OK)
        except DatabaseError:
            return handle_database_error("Database error occurred while fetching user chats.")

    @action(detail=True, methods=['post'], url_path='add-participant')
    def add_participant(self, request, pk=None):
        """Добавление пользователя в групповой чат администратором"""
        chat = self.get_object()
        if not ChatParticipant.objects.filter(chat=chat, user=request.user, role='admin').exists():
            return Response({"detail": "You do not have permission to add participants to this chat."}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        error_response = add_participant(chat, user_id)
        return error_response if error_response else Response({"detail": "Participant successfully added to chat."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='remove-participant')
    def remove_participant(self, request, pk=None):
        """Удаление пользователя из группового чата администратором"""
        chat = self.get_object()
        if not ChatParticipant.objects.filter(chat=chat, user=request.user, role='admin').exists():
            return Response({"detail": "You do not have permission to remove participants from this chat."}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        if not user_id:
            return Response({"detail": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            participant = ChatParticipant.objects.get(chat=chat, user__id=user_id)
            participant.delete()
            cache.delete(f"user_chats_{user_id}")
            cache.delete(f"chat_participants_{chat.id}")
            update_chat_cache(chat)
            return Response({"detail": "Participant successfully removed from chat."}, status=status.HTTP_200_OK)
        except ChatParticipant.DoesNotExist:
            return Response({"detail": "Participant not found in this chat."}, status=status.HTTP_404_NOT_FOUND)
        except DatabaseError:
            return handle_database_error("Database error occurred while removing participant.")


class PrivateChatViewSet(viewsets.ModelViewSet):
    queryset = PrivateChat.objects.all()
    serializer_class = PrivateChatSerializer

    def create(self, request, *args, **kwargs):
        """Создание нового личного чата между двумя участниками"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user1 = serializer.validated_data['user1']
        user2 = serializer.validated_data['user2']

        # Проверка на существование приватного чата между user1 и user2 в любом порядке
        if PrivateChat.objects.filter(user1=user1, user2=user2).exists() or PrivateChat.objects.filter(user1=user2, user2=user1).exists():
            return Response(
                {"detail": "A private chat between these participants already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создание нового приватного чата, если он не существует
        try:
            chat = PrivateChat.objects.create(user1=user1, user2=user2)
            return Response(PrivateChatSerializer(chat).data, status=status.HTTP_201_CREATED)
        except DatabaseError:
            return Response({"detail": "Database error occurred while creating private chat."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        """Удаление приватного чата вместе с его сообщениями и принудительная инвалидация кэша участников"""
        chat = self.get_object()
        try:
            # Удаляем все сообщения, связанные с этим приватным чатом
            chat.messages.all().delete()
            # Удаляем сам приватный чат
            chat.delete()

            # Инвалидация кэша для всех участников чата
            cache.delete(f"user_chats_{chat.user1.id}")
            cache.delete(f"user_chats_{chat.user2.id}")
            cache.delete(f"chat_{chat.id}")  # Удаление кэша чата по его ID

            return Response({"detail": "Private chat deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except DatabaseError:
            return handle_database_error("Database error occurred while deleting private chat.")


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def perform_create(self, serializer):
        chat_type = self.request.data.get('chat_type')  # "group" или "private"
        chat_id = self.request.data.get('chat_id')

        if chat_type == "group":
            try:
                chat = GroupChat.objects.get(id=chat_id)
                serializer.save(sender=self.request.user, group_chat=chat)
            except GroupChat.DoesNotExist:
                raise serializers.ValidationError("Group chat does not exist.")
        
        elif chat_type == "private":
            try:
                chat = PrivateChat.objects.get(id=chat_id)
                serializer.save(sender=self.request.user, private_chat=chat)
            except PrivateChat.DoesNotExist:
                raise serializers.ValidationError("Private chat does not exist.")
        else:
            raise serializers.ValidationError("Invalid chat type.")


