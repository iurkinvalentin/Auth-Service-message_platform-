from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# Устанавливаем настройки Django по умолчанию
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')

# Создаем экземпляр приложения Celery
app = Celery('auth_service')

# Задаем конфигурацию Celery через Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи из всех установленных приложений
app.autodiscover_tasks()