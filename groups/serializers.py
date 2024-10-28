from rest_framework import serializers
from groups.models import Group, GroupMembership, GroupInvitation


class GroupSerializer(serializers.ModelSerializer):
    """Сериализатор для представления и создания групп"""
    owner = serializers.ReadOnlyField(source='owner.username')
    members = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'avatar', 'created_at', 'updated_at', 'owner', 'members']

    def get_members(self, obj):
        """Получение участников группы с указанием их профиля и роли"""
        memberships = GroupMembership.objects.filter(group=obj)
        return [
            {
                'profile_id': membership.profile.id,
                'role': membership.role
            }
            for membership in memberships
        ]

    def create(self, validated_data):
        """Создание группы и добавление владельца как участника с ролью 'owner'"""
        group = Group.objects.create(**validated_data)
        GroupMembership.objects.create(
            group=group,
            profile=self.context['request'].user.profile,
            role='owner'
        )
        return group

    def update(self, instance, validated_data):
        """Обновление полей группы"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class GroupMembershipSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с членами группы"""

    class Meta:
        model = GroupMembership
        fields = ['group', 'profile', 'role', 'date_joined']

    def update(self, instance, validated_data):
        """Обновление роли участника в группе"""
        instance.role = validated_data.get('role', instance.role)
        instance.save()
        return instance


class GroupInvitationSerializer(serializers.ModelSerializer):
    """Сериализатор для приглашений в группу"""
    invited_by = serializers.ReadOnlyField(source='invited_by.user.username')
    invited_to = serializers.ReadOnlyField(source='invited_to.user.username')
    group = serializers.ReadOnlyField(source='group.name')

    class Meta:
        model = GroupInvitation
        fields = ['id', 'group', 'invited_by', 'invited_to', 'created_at', 'is_accepted']
