from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import GroupChatViewSet, MessageViewSet, PrivateChatViewSet

router = DefaultRouter()
router.register(r'chats', GroupChatViewSet, basename='chat')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'private-chats', PrivateChatViewSet, basename='private-chat') 

urlpatterns = [
    path('', include(router.urls)),
]