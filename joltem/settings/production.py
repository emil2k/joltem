""" Project's settings. """

from .core import *

ENVIRONMENT_NAME = 'production'

LOGIN_URL = 'sign_in'
LOGOUT_URL = 'sign_out'
LOGIN_REDIRECT_URL = 'home'
AUTH_PROFILE_MODULE = 'joltem.Profile'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'joltem.wsgi.application'

ROOT_URLCONF = 'joltem.urls'

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'

MIDDLEWARE_CLASSES += 'django.middleware.csrf.CsrfViewMiddleware',
INSTALLED_APPS += (

    # Contrib
    'django.contrib.markup',

    # Vendors
    'mathfilters',
    'south',

    # Project
    'joltem',
    'project',
    'solution',
    'task',
    'git',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'joltem',
        'USER': 'joltem',
        'PASSWORD': 'joltem',
        'HOST': 'localhost',
    }
}

SECRET_KEY = 'imsosecret'

logging.info("Production settings loaded.")
