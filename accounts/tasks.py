from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import CustomUser


@shared_task
def update_last_activity(user_id):
    """Обновление времени последней активности пользователя."""
    try:
        user = CustomUser.objects.get(id=user_id)
        user.profile.last_seen = timezone.now()
        user.profile.save()
    except CustomUser.DoesNotExist:
        pass


@shared_task
def send_confirmation_email(user_email, confirmation_link):
    """Задача для отправки email с подтверждением регистрации."""
    subject = "Подтверждение регистрации"
    message = f"Спасибо за регистрацию! Пожалуйста, подтвердите ваш email, перейдя по ссылке: {confirmation_link}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])
