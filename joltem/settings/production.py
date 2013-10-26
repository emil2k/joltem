""" Project's settings. """

from .core import *

ENVIRONMENT_NAME = 'production'

LOGIN_URL = 'sign_in'
LOGOUT_URL = 'sign_out'
LOGIN_REDIRECT_URL = 'home'
AUTH_PROFILE_MODULE = 'joltem.Profile'

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
    'git',
    'joltem',
    'project',
    'solution',
    'task',
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
