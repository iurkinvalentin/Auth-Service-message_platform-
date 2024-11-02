from django.db import models

from accounts.models import CustomUser
from groups.models import Group


class GroupChat(models.Model):
    """Модель для чатов групповой чат."""

    name = models.CharField(max_length=255, blank=True, null=True)
    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="chat",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name if self.name else f"Chat {self.id}"


class PrivateChat(models.Model):
    """Модель для приватных чатов между двумя участниками"""

    user1 = models.ForeignKey(
        CustomUser,
        related_name="private_chats_user1",
        on_delete=models.CASCADE,
    )
    user2 = models.ForeignKey(
        CustomUser,
        related_name="private_chats_user2",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            "user1",
            "user2",
        )  # Обеспечивает уникальность чата между двумя пользователями

    def __str__(self):
        return (
            f"Private Chat between {self.user1.username}"
            f"and {self.user2.username}"
        )


class Message(models.Model):
    """Универсальная модель для сообщений в групповых и приватных чатах."""

    content = models.TextField()
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    # Связи для разных типов чатов
    group_chat = models.ForeignKey(
        GroupChat,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="messages",
    )
    private_chat = models.ForeignKey(
        PrivateChat,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="messages",
    )

    def __str__(self):
        return (
            f"Message from {self.sender} in"
            f"{'Private Chat' if self.private_chat else 'Group Chat'}"
        )


class ChatParticipant(models.Model):
    """Модель участника чата"""

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    chat = models.ForeignKey(
        GroupChat, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default="member"
    )  # Добавляем поле role
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} in Chat {self.chat.id}"
