from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser


class Notification(models.Model):
    user = models.ForeignKey(
        CustomUser,
        verbose_name=_("Пользователь"),
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.TextField(_("Сообщение"))
    created_at = models.DateTimeField(_("Дата создания"), default=timezone.now)
    is_read = models.BooleanField(_("Прочитано"), default=False)

    def __str__(self):
        return f"Уведомление для {self.user.username}: {self.message[:20]}"

    class Meta:
        verbose_name = _("Уведомление")
        verbose_name_plural = _("Уведомления")
