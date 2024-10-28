from .celery import app as celery_app

default_app_config = 'accounts.apps.AccountsConfig'

__all__ = ('celery_app',)