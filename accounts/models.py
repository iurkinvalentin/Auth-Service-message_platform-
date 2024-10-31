from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    '''Пользовательская модель'''
    email = models.EmailField(unique=True, max_length=255)
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[RegexValidator(r'^[\w.@+-]+$')],
    )

    def __str__(self):
        return self.username


class Profile(models.Model):
    '''Модель профиля'''
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.CharField(max_length=500, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    status_message = models.CharField(max_length=255, blank=True, null=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def update_online_status(self):
        now = timezone.now()
        if self.last_seen:
            # Обновление статуса, если last_seen установлен
            self.is_online = (now - self.last_seen) < timedelta(minutes=5)
        else:
            # Если last_seen не установлен, статус offline
            self.is_online = False
        self.save()


class Connections(models.Model):
    '''Модель связей'''
    from_user = models.ForeignKey(CustomUser,
                                  related_name='outgoing_connections',
                                  on_delete=models.CASCADE)
    to_user = models.ForeignKey(CustomUser,
                                related_name='incoming_connections',
                                on_delete=models.CASCADE)
    is_confirmed = models.BooleanField(default=False)  # Если двусторонняя связь, дружба подтверждена
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['from_user', 'to_user'], name='unique_connection')
        ]

    def __str__(self):
        return f"{self.from_user.username} is connected with {self.to_user.username}"

