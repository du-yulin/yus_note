import os
import django
from django.conf import settings
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yus_note.settings')
django.setup()

celery_app = Celery('yus_note')

celery_app.config_from_object(settings)

celery_app.autodiscover_tasks()


