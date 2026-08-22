"""
Minimal Django settings used to run the django-gc test suite.
"""

from pathlib import Path
from typing import Any

from tests.definitions import TEST_CATEGORIES, TEST_DEFINITIONS

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY: str = 'django-gc-test-secret-key'

DEBUG: bool = True

USE_TZ: bool = True

ALLOWED_HOSTS: list[str] = ['testserver']

INSTALLED_APPS: list[str] = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_gc',
]

MIDDLEWARE: list[str] = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF: str = 'tests.urls'

TEMPLATES: list[dict[str, Any]] = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ]
        },
    }
]

DATABASES: dict[str, dict[str, str]] = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}

CACHES: dict[str, dict[str, Any]] = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'django-gc-tests',
        'TIMEOUT': None,
    }
}

STORAGES: dict[str, dict[str, str]] = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    'media': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
}

STATIC_URL: str = '/static/'
MEDIA_URL: str = '/media/'
MEDIA_ROOT: str = str(BASE_DIR / '.tmp' / 'media')

DEFAULT_AUTO_FIELD: str = 'django.db.models.BigAutoField'

GLOBAL_CONFIG_CATEGORIES = TEST_CATEGORIES
GLOBAL_CONFIG_DEFINITIONS = TEST_DEFINITIONS
GLOBAL_CONFIG_ENCRYPTION_KEY = 'django-gc-test-encryption-key'
