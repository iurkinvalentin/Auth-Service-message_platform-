from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser
from groups.models import Group


class GroupChat(models.Model):
    """Модель для чатов групповой чат."""

    name = models.CharField(
        _("Название"), max_length=255, blank=True, null=True
    )
    group = models.OneToOneField(
        Group,
        verbose_name=_("Группа"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="chat",
    )
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)

    def __str__(self):
        return self.name if self.name else f"Chat {self.id}"

    class Meta:
        verbose_name = _("Групповой чат")
        verbose_name_plural = _("Групповые чаты")


class PrivateChat(models.Model):
    """Модель для приватных чатов между двумя участниками"""

    user1 = models.ForeignKey(
        CustomUser,
        verbose_name=_("Пользователь 1"),
        related_name="private_chats_user1",
        on_delete=models.CASCADE,
    )
    user2 = models.ForeignKey(
        CustomUser,
        verbose_name=_("Пользователь 2"),
        related_name="private_chats_user2",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)

    class Meta:
        unique_together = ("user1", "user2")
        verbose_name = _("Приватный чат")
        verbose_name_plural = _("Приватные чаты")

    def __str__(self):
        return (
            f"Private Chat between"
            f"{self.user1.username} and {self.user2.username}"
        )


class Message(models.Model):
    """Универсальная модель для сообщений в групповых и приватных чатах."""

    content = models.TextField(_("Содержание"))
    sender = models.ForeignKey(
        CustomUser, verbose_name=_("Отправитель"), on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(_("Дата отправки"), auto_now_add=True)

    group_chat = models.ForeignKey(
        GroupChat,
        verbose_name=_("Групповой чат"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="messages",
    )
    private_chat = models.ForeignKey(
        PrivateChat,
        verbose_name=_("Приватный чат"),
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

    class Meta:
        verbose_name = _("Сообщение")
        verbose_name_plural = _("Сообщения")


class ChatParticipant(models.Model):
    """Модель участника чата"""

    ROLE_CHOICES = [
        ("admin", _("Администратор")),
        ("member", _("Участник")),
    ]

    chat = models.ForeignKey(
        GroupChat,
        verbose_name=_("Чат"),
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        CustomUser, verbose_name=_("Пользователь"), on_delete=models.CASCADE
    )
    role = models.CharField(
        _("Роль"), max_length=10, choices=ROLE_CHOICES, default="member"
    )
    joined_at = models.DateTimeField(
        _("Дата присоединения"), auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} в чате {self.chat.id}"

    class Meta:
        verbose_name = _("Участник чата")
        verbose_name_plural = _("Участники чатов")
