"""
Test settings for conversations app.
"""

from decouple import config

# Test database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use in-memory database for tests
USE_TZ = True

# Test-specific settings
SECRET_KEY = 'test-secret-key-for-conversations-tests'

# Installed apps for testing
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'apps.users',
    'apps.conversations',
]

# REST Framework settings for tests
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT settings for tests
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': 3600,  # 1 hour
    'REFRESH_TOKEN_LIFETIME': 86400,  # 24 hours
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Spectacular settings for tests
SPECTACULAR_SETTINGS = {
    'TITLE': 'Test API',
    'DESCRIPTION': 'Test API documentation',
    'VERSION': '1.0.0',
}
