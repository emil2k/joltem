""" Project's settings. """
from datetime import timedelta

from .core import *


ENVIRONMENT_NAME = 'production'

URL = 'joltem.com'
LOGIN_URL = 'sign_in'
LOGOUT_URL = 'sign_out'
LOGIN_REDIRECT_URL = 'home'
AUTH_USER_MODEL = 'joltem.User'
BASE_FROM_EMAIL = 'support@joltem.com'
NOTIFY_FROM_EMAIL = BASE_FROM_EMAIL
ALLOWED_HOSTS = [
    ".joltem.com", ".joltem.com.", ".joltem.local", ".joltem.local."]

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'joltem.wsgi.application'

ROOT_URLCONF = 'joltem.urls'

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'

MIDDLEWARE_CLASSES += 'django.middleware.csrf.CsrfViewMiddleware',
INSTALLED_APPS += (

    # Contrib
    'markup_deprecated',

    # Vendors
    'mathfilters',
    'south',
    'widget_tweaks',

    # Project
    'joltem',
    'project',
    'solution',
    'task',
    'git',
    'help',
    'account',
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

SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS_URL = 'redis://localhost:6379/0'

CACHES['default']['BACKEND'] = 'redis_cache.RedisCache'
CACHES['default']['LOCATION'] = 'localhost:6379'
CACHES['default']['OPTIONS'] = {
    'DB': 1, 'PASSWORD': '', 'PARSER_CLASS': 'redis.connection.HiredisParser'}
CACHES['default']['KEY_PREFIX'] = '_'.join((PROJECT_NAME, ENVIRONMENT_NAME))

SECRET_KEY = 'imsosecret'

# Gateway settings
GATEWAY_PORT = 22
GATEWAY_HOST = 'joltem.com'
GATEWAY_DIR = op.join(PROJECT_ROOT, 'gateway')
GATEWAY_REPOSITORIES_DIR = op.join(GATEWAY_DIR, 'repositories')
GATEWAY_PRIVATE_KEY_FILE_PATH = op.join(GATEWAY_DIR, 'id_rsa')
GATEWAY_PUBLIC_KEY_FILE_PATH = op.join(GATEWAY_DIR, 'id_rsa.pub')

# Celery settings
BROKER_URL = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']

CELERYBEAT_SCHEDULE = {
    'daily-diggest': {
        'task': 'joltem.tasks.daily_diggest',
        'schedule': timedelta(hours=24),
        'args': (),
    }
}

# Authomatic settings
from authomatic.providers import oauth2, oauth1
import authomatic

AUTHOMATIC = {

    'twitter': {
        'id': authomatic.provider_id(),
        'class_': oauth1.Twitter,
        'consumer_key': 'pS3vnCVoC91AAyXPD9Oog',
        'consumer_secret': 'ZYHUSJsxwdmJp4U3EtE8OJprymb8JIiiwXimQ17V04',
        'profile_url': 'http://twitter.com/{username}',
    },

    'facebook': {
        'id': authomatic.provider_id(),
        'class_': oauth2.Facebook,
        'consumer_key': '426893780769525',
        'consumer_secret': '5124dcc7a27fb858f7172299fcd48abe',
        'scope': ['email'],
        'profile_url': 'http://facebook.com/{username}',
    },

    'github': {
        'id': authomatic.provider_id(),
        'class_': oauth2.GitHub,
        'consumer_key': 'c2225b4da7ac43f56d22',
        'consumer_secret': '641c458a2170d7f922576b0cd6b00713f2726d0f',
        'scope': ['user:email'],
        'profile_url': 'http://github.com/{username}',
    },

    'bitbucket': {
        'id': authomatic.provider_id(),
        'class_': oauth1.Bitbucket,
        'consumer_key': 'Ph9TEyPMRgP6TYb9tt',
        'consumer_secret': 'dQ9xHmu3AZfzHjYKRg2eKNFgKUNHCdA3',
        'profile_url': 'http://bitbucket.com/{username}',
    }

}


TEMPLATE_CONTEXT_PROCESSORS += 'settings_context_processor.context_processors.settings', # noqa
TEMPLATE_VISIBLE_SETTINGS = 'DEBUG',

logging.info("Production settings loaded.")
