from celery import shared_task
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