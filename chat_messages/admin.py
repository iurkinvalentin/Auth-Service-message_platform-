from django.contrib import admin
from .models import GroupChat, PrivateChat, Message, ChatParticipant


class GroupChatAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "group", "created_at")
    search_fields = ("name", "group__name")
    list_filter = ("created_at",)
    ordering = ("id",)

    def get_participant_count(self, obj):
        return obj.participants.count()
    get_participant_count.short_description = "Participant Count"


class PrivateChatAdmin(admin.ModelAdmin):
    list_display = ("id", "user1", "user2", "created_at")
    search_fields = ("user1__username", "user2__username")
    list_filter = ("created_at",)
    ordering = ("created_at",)

    def __str__(self):
        return f"Private chat between {self.user1} and {self.user2}"


class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "content", "created_at", "chat_type")
    search_fields = ("sender__username", "content")
    list_filter = ("created_at",)

    def chat_type(self, obj):
        return "Group" if obj.group_chat else "Private"
    chat_type.short_description = "Chat Type"


class ChatParticipantAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "user", "role", "joined_at")
    search_fields = ("user__username", "chat__name")
    list_filter = ("role", "joined_at")
    ordering = ("chat", "user")


admin.site.register(GroupChat, GroupChatAdmin)
admin.site.register(PrivateChat, PrivateChatAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(ChatParticipant, ChatParticipantAdmin)
