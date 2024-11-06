from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser, Profile


class Group(models.Model):
    name = models.CharField(_("Название"), max_length=255)
    avatar = models.ImageField(
        _("Аватар"), upload_to="avatars/", null=True, blank=True
    )
    description = models.TextField(_("Описание"), blank=True)
    owner = models.ForeignKey(
        CustomUser, verbose_name=_("Владелец"), on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Дата обновления"), auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Группа")
        verbose_name_plural = _("Группы")


class GroupMembership(models.Model):
    ROLE_CHOICES = [
        ("owner", _("Владелец")),
        ("member", _("Участник")),
    ]
    group = models.ForeignKey(
        Group, verbose_name=_("Группа"), on_delete=models.CASCADE
    )
    profile = models.ForeignKey(
        Profile, verbose_name=_("Профиль"), on_delete=models.CASCADE
    )
    role = models.CharField(
        _("Роль"), max_length=10, choices=ROLE_CHOICES, default="member"
    )
    date_joined = models.DateTimeField(
        _("Дата присоединения"), auto_now_add=True
    )

    class Meta:
        unique_together = ("group", "profile")
        verbose_name = _("Участие в группе")
        verbose_name_plural = _("Участия в группах")

    def is_owner(self):
        return self.role == "owner"


class GroupInvitation(models.Model):
    group = models.ForeignKey(
        Group, verbose_name=_("Группа"), on_delete=models.CASCADE
    )
    invited_by = models.ForeignKey(
        Profile,
        verbose_name=_("Пригласил"),
        on_delete=models.CASCADE,
        related_name="invitations_sent",
    )
    invited_to = models.ForeignKey(
        Profile,
        verbose_name=_("Приглашен"),
        on_delete=models.CASCADE,
        related_name="invitations_received",
    )
    created_at = models.DateTimeField(_("Дата приглашения"), auto_now_add=True)
    is_accepted = models.BooleanField(_("Принято"), default=False)

    def __str__(self):
        return (
            f"Приглашение в {self.group.name} от "
            f"{self.invited_by.user.username} к "
            f"{self.invited_to.user.username}"
        )

    class Meta:
        verbose_name = _("Приглашение")
        verbose_name_plural = _("Приглашения")
