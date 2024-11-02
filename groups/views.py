from django.core.cache import cache
from django.db import DatabaseError, IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response

from accounts.models import Profile
from groups.models import Group, GroupInvitation, GroupMembership
from groups.serializers import GroupInvitationSerializer, GroupSerializer


def is_owner(user, group):
    """Проверка, является ли пользователь владельцем группы"""
    return GroupMembership.objects.filter(
        group=group, profile=user.profile, role="owner"
    ).exists()


def handle_database_error(detail_message):
    """Обработчик ошибок базы данных"""
    return Response(
        {"detail": detail_message},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


class GroupViewSet(viewsets.ViewSet):
    """Представление для управления группами и участниками"""

    def list(self, request):
        """Получить список всех групп"""
        cache_key = "all_groups"
        groups_data = cache.get(cache_key)

        if not groups_data:
            try:
                groups = Group.objects.all()
                serializer = GroupSerializer(groups, many=True)
                groups_data = serializer.data
                cache.set(
                    cache_key, groups_data, timeout=300
                )  # Кэшируем на 5 минут
            except DatabaseError:
                return handle_database_error(
                    "Ошибка базы данных при получении списка групп"
                )

        return Response(groups_data)

    def create(self, request):
        """Создание новой группы и назначение владельца"""
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            try:
                group = Group.objects.create(
                    name=serializer.validated_data["name"],
                    description=serializer.validated_data["description"],
                    avatar=serializer.validated_data.get("avatar", None),
                    owner=request.user,
                )
                GroupMembership.objects.create(
                    group=group, profile=request.user.profile, role="owner"
                )
                return Response(
                    GroupSerializer(group).data, status=status.HTTP_201_CREATED
                )
            except IntegrityError:
                return Response(
                    {"detail": "Группа с таким именем уже существует"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except DatabaseError:
                return handle_database_error(
                    "Ошибка базы данных при создании группы"
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """Получение конкретной группы по id"""
        cache_key = f"group_{pk}"
        group_data = cache.get(cache_key)

        if not group_data:
            try:
                group = get_object_or_404(Group, pk=pk)
                serializer = GroupSerializer(group)
                group_data = serializer.data
                cache.set(
                    cache_key, group_data, timeout=300
                )  # Кэшируем на 5 минут
            except DatabaseError:
                return handle_database_error(
                    "Ошибка базы данных при получении группы"
                )

        return Response(group_data)

    def partial_update(self, request, pk=None):
        """Частичное обновление группы"""
        group = get_object_or_404(Group, pk=pk)
        serializer = GroupSerializer(group, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except DatabaseError:
                return Response(
                    {"detail": "Ошибка базы данных при обновлении группы"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Обновление существующей группы"""
        group = get_object_or_404(Group, pk=pk)
        serializer = GroupSerializer(group, data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                cache.delete(f"group_{pk}")  # Удаляем кэш группы
                return Response(serializer.data)
            except DatabaseError:
                return handle_database_error(
                    "Ошибка базы данных при обновлении группы"
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Удаление группы"""
        group = get_object_or_404(Group, pk=pk)
        try:
            group.delete()
            cache.delete(f"group_{pk}")  # Удаляем кэш группы
            cache.delete("all_groups")  # Удаляем кэш списка групп
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DatabaseError:
            return handle_database_error(
                "Ошибка базы данных при удалении группы"
            )

    def remove_members(self, request, pk=None):
        """Удаление участников из группы"""
        group = get_object_or_404(Group, pk=pk)
        if not is_owner(request.user, group):
            return Response(
                {"detail": "У вас нет прав удалять участников"},
                status=status.HTTP_403_FORBIDDEN,
            )

        members_data = request.data.get("members", [])
        for member_id in members_data:
            member_profile = get_object_or_404(Profile, pk=member_id)
            membership = GroupMembership.objects.filter(
                group=group, profile=member_profile
            ).first()
            if membership:
                try:
                    membership.delete()
                except DatabaseError:
                    return handle_database_error(
                        "Ошибка базы данных при удалении участника"
                    )
            else:
                return Response(
                    {
                        "detail": f"Участник с ID {member_id} не найден"
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(
            {"detail": "Участники успешно удалены"}, status=status.HTTP_200_OK
        )

    def add_members(self, request, pk=None):
        """Добавление участника в группу"""
        group = get_object_or_404(Group, pk=pk)
        member_profile = get_object_or_404(
            Profile, pk=request.data.get("profile_id")
        )

        if not is_owner(request.user, group):
            return Response(
                {"detail": "У вас нет прав добавлять участников"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if GroupMembership.objects.filter(
            group=group, profile=member_profile
        ).exists():
            return Response(
                {"detail": "Этот участник уже состоит в группе"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            GroupMembership.objects.create(
                group=group, profile=member_profile, role="member"
            )
            return Response(
                {"detail": "Участник успешно добавлен"},
                status=status.HTTP_200_OK,
            )
        except IntegrityError:
            return Response(
                {"detail": "Ошибка добавления участника"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def change_role(self, request, pk=None):
        """Изменение роли участника (может делать только владелец)"""
        group = get_object_or_404(Group, pk=pk)
        member_profile = get_object_or_404(
            Profile, pk=request.data.get("profile_id")
        )
        new_role = request.data.get("role")

        if new_role not in dict(GroupMembership.ROLE_CHOICES):
            return Response(
                {"detail": "Недопустимая роль"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not is_owner(request.user, group):
            return Response(
                {"detail": "У вас нет прав изменять роли"},
                status=status.HTTP_403_FORBIDDEN,
            )

        membership = get_object_or_404(
            GroupMembership, group=group, profile=member_profile
        )
        try:
            membership.role = new_role
            membership.save()
            return Response(
                {"detail": "Роль успешно изменена"}, status=status.HTTP_200_OK
            )
        except DatabaseError:
            return handle_database_error(
                "Ошибка базы данных при изменении роли"
            )


class InvitationViewSet(viewsets.ViewSet):
    """Представление для управления приглашениями в группу"""

    def create(self, request):
        """Отправка приглашения в группу"""
        group_id = request.data.get("group_id")
        invited_to_profile_id = request.data.get("profile_id")
        group = get_object_or_404(Group, pk=group_id)
        invited_to_profile = get_object_or_404(
            Profile, pk=invited_to_profile_id
        )

        if not GroupMembership.objects.filter(
            group=group,
            profile=request.user.profile,
            role__in=["owner", "admin"],
        ).exists():
            return Response(
                {
                    "detail": "У вас нет прав приглашать пользователей"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if GroupInvitation.objects.filter(
            group=group, invited_to=invited_to_profile
        ).exists():
            return Response(
                {"detail": "Приглашение уже отправлено"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            invitation = GroupInvitation.objects.create(
                group=group,
                invited_by=request.user.profile,
                invited_to=invited_to_profile,
            )
            return Response(
                GroupInvitationSerializer(invitation).data,
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError:
            return Response(
                {"detail": "Ошибка при создании приглашения"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def accept(self, request, pk=None):
        """Принятие приглашения в группу"""
        invitation = get_object_or_404(
            GroupInvitation, pk=pk, invited_to=request.user.profile
        )
        if invitation.is_accepted:
            return Response(
                {"detail": "Это приглашение уже принято"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            invitation.is_accepted = True
            invitation.save()
            GroupMembership.objects.create(
                group=invitation.group,
                profile=invitation.invited_to,
                role="member",
            )
            return Response(
                {"detail": "Приглашение принято, вы добавлены в группу"},
                status=status.HTTP_200_OK,
            )
        except DatabaseError:
            return handle_database_error(
                "Ошибка базы данных при принятии приглашения"
            )

    def decline(self, request, pk=None):
        """Отклонение приглашения в группу"""
        invitation = get_object_or_404(
            GroupInvitation, pk=pk, invited_to=request.user.profile
        )
        if invitation.is_accepted:
            return Response(
                {
                    "detail": "Это приглашение уже принято"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            invitation.delete()
            return Response(
                {"detail": "Приглашение отклонено"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except DatabaseError:
            return handle_database_error(
                "Ошибка базы данных при отклонении приглашения"
            )
