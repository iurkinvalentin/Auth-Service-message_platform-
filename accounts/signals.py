from django.dispatch import receiver
from .models import CustomUser, Profile, Connections
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


# Очистка кэша после сохранения профиля
@receiver(post_save, sender=Profile)
def clear_profile_cache(sender, instance, **kwargs):
    cache_key = f"profile_{instance.user.id}"
    cache.delete(cache_key)

# Очистка кэша после удаления профиля
@receiver(post_delete, sender=Profile)
def clear_deleted_profile_cache(sender, instance, **kwargs):
    cache_key = f"profile_{instance.user.id}"
    cache.delete(cache_key)


# Очистка кэша контактов при добавлении или удалении связи
@receiver([post_save, post_delete], sender=Connections)
def clear_connections_cache(sender, instance, **kwargs):
    # Очистка кэша для пользователей обеих сторон связи
    for user in [instance.from_user, instance.to_user]:
        cache_key = f"confirmed_contacts_{user.id}"
        cache.delete(cache_key)