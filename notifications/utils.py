# notifications/utils.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification

def send_notification(user, message):
    # Сохраняем уведомление в базе данных
    Notification.objects.create(user=user, message=message)
    
    # Отправляем уведомление через WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{user.id}",
        {
            'type': 'send_notification',
            'message': message,
        }
    )
