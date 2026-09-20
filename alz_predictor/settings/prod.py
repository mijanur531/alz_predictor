from .base import *

DEBUG = False

# Read DB URL from environment in production
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://postgres:postgres@db:5432/alz_db')
}

# Security settings checklist
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Static files storage and extra caching in production
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
