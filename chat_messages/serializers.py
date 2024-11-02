from asgiref.sync import sync_to_async
from rest_framework import serializers

from accounts.models import CustomUser

from .models import ChatParticipant, GroupChat, Message, PrivateChat


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source="sender.username")
    chat_type = serializers.ChoiceField(
        choices=[("group", "Group Chat"), ("private", "Private Chat")],
        write_only=True,
    )
    chat_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "content",
            "sender",
            "created_at",
            "chat_type",
            "chat_id",
            "group_chat",
            "private_chat",
        ]
        read_only_fields = ["group_chat", "private_chat"]

    async def validate(self, attrs):
        chat_type = attrs.get("chat_type")
        chat_id = attrs.get("chat_id")

        if chat_type == "group":
            try:
                attrs["group_chat"] = await sync_to_async(
                    GroupChat.objects.get
                )(id=chat_id)
                attrs["private_chat"] = (
                    None
                )
            except GroupChat.DoesNotExist:
                raise serializers.ValidationError("Group chat does not exist.")

        elif chat_type == "private":
            try:
                attrs["private_chat"] = await sync_to_async(
                    PrivateChat.objects.get
                )(id=chat_id)
                attrs["group_chat"] = (
                    None
                )
            except PrivateChat.DoesNotExist:
                raise serializers.ValidationError(
                    "Private chat does not exist."
                )

        else:
            raise serializers.ValidationError("Invalid chat type.")

        return attrs

    async def create(self, validated_data):
        validated_data.pop("chat_type")
        validated_data.pop("chat_id")

        return await sync_to_async(Message.objects.create)(**validated_data)


class ChatParticipantSerializer(serializers.ModelSerializer):
    user = serializers.CharField(
        source="user.username"
    )

    class Meta:
        model = ChatParticipant
        fields = ["id", "user", "role"]


class GroupChatSerializer(serializers.ModelSerializer):
    participants = ChatParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = GroupChat
        fields = ["id", "name", "participants", "created_at"]

    def create(self, validated_data):
        participants_data = validated_data.pop("participants", [])

        chat = GroupChat.objects.create(**validated_data)

        for user in participants_data:
            ChatParticipant.objects.create(chat=chat, user=user)

        return chat

    def update(self, instance, validated_data):
        participants_data = validated_data.pop("participants", None)

        instance.name = validated_data.get("name", instance.name)
        instance.save()

        if participants_data is not None:
            instance.participants.clear()
            for user in participants_data:
                ChatParticipant.objects.create(chat=instance, user=user)

        return instance


class PrivateChatSerializer(serializers.ModelSerializer):
    user1 = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )
    user2 = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    class Meta:
        model = PrivateChat
        fields = ["id", "user1", "user2", "created_at"]

    def validate(self, data):
        """Проверка на существование приватного чата между двумя участниками"""
        user1 = data["user1"]
        user2 = data["user2"]
        if (
            PrivateChat.objects.filter(user1=user1, user2=user2).exists()
            or PrivateChat.objects.filter(user1=user2, user2=user1).exists()
        ):
            raise serializers.ValidationError(
                "A private chat between these participants already exists."
            )
        return data

    def create(self, validated_data):
        """Создание нового приватного чата между двумя участниками"""
        return PrivateChat.objects.create(**validated_data)
