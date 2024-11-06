from django.db import models
from django.utils.translation import gettext_lazy as _


class GroupChat(models.Model):
    name = models.CharField(_("Название чата"), max_length=100)
    group = models.ForeignKey(
        "Group", verbose_name=_("Группа"), on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)

    class Meta:
        verbose_name = _("Групповой чат")
        verbose_name_plural = _("Групповые чаты")


class PrivateChat(models.Model):
    user1 = models.ForeignKey(
        "User",
        verbose_name=_("Пользователь 1"),
        on_delete=models.CASCADE,
        related_name="private_chats_user1",
    )
    user2 = models.ForeignKey(
        "User",
        verbose_name=_("Пользователь 2"),
        on_delete=models.CASCADE,
        related_name="private_chats_user2",
    )
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)

    class Meta:
        verbose_name = _("Приватный чат")
        verbose_name_plural = _("Приватные чаты")


class Message(models.Model):
    sender = models.ForeignKey(
        "User", verbose_name=_("Отправитель"), on_delete=models.CASCADE
    )
    content = models.TextField(_("Сообщение"))
    created_at = models.DateTimeField(_("Дата отправки"), auto_now_add=True)
    group_chat = models.ForeignKey(
        GroupChat,
        verbose_name=_("Групповой чат"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    private_chat = models.ForeignKey(
        PrivateChat,
        verbose_name=_("Приватный чат"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Сообщение")
        verbose_name_plural = _("Сообщения")


class ChatParticipant(models.Model):
    chat = models.ForeignKey(
        GroupChat, verbose_name=_("Чат"), on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        "User", verbose_name=_("Пользователь"), on_delete=models.CASCADE
    )
    role = models.CharField(_("Роль"), max_length=50)
    joined_at = models.DateTimeField(
        _("Дата присоединения"), auto_now_add=True
    )

    class Meta:
        verbose_name = _("Участник чата")
        verbose_name_plural = _("Участники чатов")
