import os
from celery import Celery

# Set default Django settings module for celery program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alz_predictor.settings.dev')

app = Celery('alz_predictor')

# Config from django settings, prefixed with 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
