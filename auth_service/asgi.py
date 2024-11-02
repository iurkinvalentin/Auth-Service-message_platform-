import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "auth_service.settings")
application = get_asgi_application()  # Вызовите get_asgi_application здесь

from channels.routing import ProtocolTypeRouter, URLRouter

import notifications.routing
from chat_messages.middleware import JWTAuthMiddleware
from chat_messages.routing import \
    websocket_urlpatterns as chat_websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": application,
        "websocket": JWTAuthMiddleware(
            URLRouter(
                notifications.routing.websocket_urlpatterns
                + chat_websocket_urlpatterns
            )
        ),
    }
)
