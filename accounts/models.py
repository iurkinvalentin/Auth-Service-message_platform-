from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """Модель пользователя"""

    email = models.EmailField(
        _("Электронная почта"), unique=True, max_length=255
    )
    username = models.CharField(
        _("Имя пользователя"),
        max_length=150,
        unique=True,
        validators=[RegexValidator(r"^[\w.@+-]+$")],
    )

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")


class Profile(models.Model):
    """Модель профиля"""

    user = models.OneToOneField(
        CustomUser, verbose_name=_("Пользователь"), on_delete=models.CASCADE
    )
    bio = models.CharField(
        _("Биография"), max_length=500, null=True, blank=True
    )
    avatar = models.ImageField(
        _("Аватар"), upload_to="avatars/", null=True, blank=True
    )
    birthday = models.DateField(_("Дата рождения"), null=True, blank=True)
    status_message = models.CharField(
        _("Статусное сообщение"), max_length=255, blank=True, null=True
    )
    is_online = models.BooleanField(_("В сети"), default=False)
    last_seen = models.DateTimeField(
        _("Последний визит"), null=True, blank=True
    )

    def __str__(self):
        return f"{self.user.username} — профиль"

    def update_online_status(self):
        now = timezone.now()
        if self.last_seen:
            self.is_online = (now - self.last_seen) < timedelta(minutes=5)
        else:
            self.is_online = False
        self.save()

    class Meta:
        verbose_name = _("Профиль")
        verbose_name_plural = _("Профили")


class Connections(models.Model):
    """Модель связей"""

    from_user = models.ForeignKey(
        CustomUser,
        verbose_name=_("От кого"),
        related_name="outgoing_connections",
        on_delete=models.CASCADE,
    )
    to_user = models.ForeignKey(
        CustomUser,
        verbose_name=_("К кому"),
        related_name="incoming_connections",
        on_delete=models.CASCADE,
    )
    is_confirmed = models.BooleanField(_("Подтверждено"), default=False)
    created = models.DateTimeField(_("Дата создания"), auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user"], name="unique_connection"
            )
        ]
        verbose_name = _("Связь")
        verbose_name_plural = _("Связи")

    def __str__(self):
        return f"{self.from_user.username} — связь с {self.to_user.username}"
