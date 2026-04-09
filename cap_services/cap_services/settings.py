"""
Django settings for cap_services project.
"""
#SG- recovery code : KUR1LBQ578R5ACJ14CK69QH8

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$=yd7(77sgpz*&!(-8smpt8kfk1d-f50z38uq#0w4bia-3xrog'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = [
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third party
    'crispy_forms',
    'crispy_bootstrap5',
    
    # Custom apps
    'core',
    'accounts',
    'store',
    'orders',
    'staff',
    'admin_panel',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cap_services.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'cap_services.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation (disabled for now)
AUTH_PASSWORD_VALIDATORS = []


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

ALLOWED_HOSTS=['localhost', '127.0.0.1', 'sreeharismadhav.local', '192.168.1.7',]#'capservicers.com', 'www.capservicers.com']


# Custom settings
SITE_NAME = 'CAP Services'
SITE_URL = 'http://localhost:8000'
SITE_EMAIL = 'capservicers@gmail.com'
SITE_PHONE = '7510158899, 9744552007'

"""# cap_services/settings.py - Add at the bottom

import os
from dotenv import load_dotenv

load_dotenv()

# SendGrid SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = os.getenv('SENDGRID_API_KEY')  # Your API key here
DEFAULT_FROM_EMAIL = 'CAP Services <noreply@capservicers.com>'"""

# cap_services/settings.py

"""EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = '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'  # Your actual API key
DEFAULT_FROM_EMAIL = 'CAP Services <noreply@capservicers.com>'"""

# cap_services/settings.py

"""SENDGRID_API_KEY = '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'
DEFAULT_FROM_EMAIL = 'CAP Services <noreply@capservicers.com>'"""

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'sreeharismadhav@gmail.com'
EMAIL_HOST_PASSWORD = 'ydwlwtxqaupmcnba'
DEFAULT_FROM_EMAIL = 'CAP Services <noreply@capservicers.com>'