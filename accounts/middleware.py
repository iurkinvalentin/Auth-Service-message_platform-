from .tasks import update_last_activity


class LastActivityMiddleware:
    """Middleware для отслеживания активности пользователя."""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Обновляем активность пользователя, если он аутентифицирован
        if request.user.is_authenticated:
            update_last_activity.delay(request.user.id)
        
        return response
