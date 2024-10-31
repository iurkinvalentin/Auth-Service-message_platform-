# notifications/urls.py
from django.urls import path

from .views import NotificationViewSet

urlpatterns = [
    path('notifications/', NotificationViewSet.as_view({'get': 'list'}), name='notification-list'),
    path('notifications/<int:pk>/read/', NotificationViewSet.as_view({'post': 'mark_as_read'}), name='notification-mark-as-read'),
]
