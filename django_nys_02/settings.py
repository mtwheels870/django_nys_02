"""
Django settings for DJANGO project.

Generated by 'django-admin startproject' using Django 4.2.16.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-o$n17$$v!&omhuiy$24im(leupmj$p-7xi(!8#)z76i1(2tsf0'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "18.208.200.162", 
    "127.0.0.1",
    "www.pinp01nt.com"
]

INSTALLED_APPS = [
    'channels',
    'daphne',
    'powerscan.apps.PowerScanConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rest_framework',
    'rest_framework_gis',
    'debug_toolbar',
    'djangobower',
    'django_extensions',
    'kg_admin.apps.KgAdminConfig',
    'kg_train.apps.KgTrainConfig',
    'colorfield',
    'django_prose_editor',
    'django_tables2', 
    'django_celery_results',     
    'django_celery_beat',     
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'django_nys_02.urls'

# MTW: Can override default templates here
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'django_nys_02.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
# 'ENGINE': 'django.db.backends.postgresql_psycopg2',

# Ternery style    DIR_ZMAP_NAME = 'production' if PRODUCTION_MODE else 'development'
PRODUCTION_MODE = False
if PRODUCTION_MODE:
    DIR_ZMAP_NAME = 'production' 
    CELERY_APP_NAME = "celery_django_prod"
    CELERY_QUEUE = "cb_production"
    PRODIGY_PORT = 8081 
else:
    DIR_ZMAP_NAME = 'development'
    CELERY_APP_NAME = "celery_django_dev"
    CELERY_QUEUE = 'cb_development'
    PRODIGY_PORT = 8080 

# PRODUCTION.  NAME /compassblue01/cb_production/,
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'cb_production' if PRODUCTION_MODE else 'compassblue01',
        'USER': 'cb_admin',
        'PASSWORD': 'Ch0c0late!',
        'HOST': 'localhost',
        'PORT': '5432',
    },
    'secondary': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'prodigy',
        'USER': 'cb_admin',
        'PASSWORD': 'Ch0c0late!',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# This is a little weird that we're in the kg_train part of the world (and not the top-level like django_nys_02
DATABASE_ROUTERS = ['kg_train.routers.SecondaryRouter']

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

# WAS TIME_ZONE = 'UTC'
TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# MTW, need to put the alias in the Apache file as well (should be done).
# python manage.py collectstatic
STATIC_ROOT = '/home/bitnami/CompassBlue/django_nys_02/static'

# MTW, added from scheduler / calendar shit
# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'djangobower.finders.BowerFinder',
)

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

import os

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            # "level": "ERROR",
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "ERROR",
    },
    'loggers': {
        '': {           # root logger
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'powerscan.*': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.channels.worker': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'powerscan.consumers': {  # Add logger for your consumers
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}

BOWER_INSTALLED_APPS = (
    'jquery',
    'jquery-ui',
    'bootstrap',
    'fullcalendar#3.8.2'
)

# Directory where uploaded files will be stored
MEDIA_ROOT = BASE_DIR / 'media'

# URL for accessing uploaded files
MEDIA_URL = '/media/'

# Celery Configuration Options
CELERY_TIMEZONE = "America/New_York"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Use Redis as the message broker
CELERY_RESULT_BACKEND = 'django-db'  # Use Django database as result backend
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_WORKER_CANCEL_LONG_RUNNING_TASKS_ON_CONNECTION_LOSS = True
CELERYBEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# This probably works b/c the web socket stuff gets through
ASGI_APPLICATION = "django_nys_02.asgi.application"

#            "hosts": [("127.0.0.1", 6379)],
#        "BACKEND": "channels_redis.core.RedisChannelLayer",
#        "CONFIG": {
#            "hosts": [("localhost", 6379)],
#        "BACKEND": "channels.layers.InMemoryChannelLayer",
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
        },
        "ROUTING": ".asgi.application",
    },
}


