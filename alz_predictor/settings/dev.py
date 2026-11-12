from .base import *

DEBUG = True

# Windows compatibility: exclude daphne from INSTALLED_APPS in dev to prevent Twisted reactor deadlock
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'daphne']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

import socket

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
print("Offline dev mode: InMemoryChannelLayer, eager Celery, native Django server.")


