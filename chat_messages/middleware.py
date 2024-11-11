import jwt
from channels.db import database_sync_to_async
from django.conf import settings

from accounts.models import CustomUser


@database_sync_to_async
def get_user_from_token(token):
    """Получает пользователя из JWT-токена или возвращает None."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user = CustomUser.objects.get(id=payload["user_id"])
        return user
    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
        CustomUser.DoesNotExist,
    ):
        return None


class JWTAuthMiddleware:
    """Промежуточный слой для аутентификации JWT-токеном."""

    def __init__(self, inner):
        """Инициализирует middleware с вложенным приложением."""
        self.inner = inner

    async def __call__(self, scope, receive, send):
        """Проверяет JWT-токен в заголовках."""
        headers = dict(scope["headers"])
        token = headers.get(b"authorization", b"").decode().split(" ")
        if len(token) == 2 and token[0] == "Bearer":
            scope["user"] = await get_user_from_token(token[1])
        else:
            scope["user"] = None
        return await self.inner(scope, receive, send)
