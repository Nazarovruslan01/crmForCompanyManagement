"""Celery configuration for async tasks."""
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

app = Celery('crm_backend')
app.config_from_object('config.settings.base', namespace='CELERY')
app.autodiscover_tasks()
