""" Project's settings. """
from datetime import timedelta

from .core import *


ENVIRONMENT_NAME = 'production'

URL = 'joltem.com'
LOGIN_URL = 'sign_in'
LOGOUT_URL = 'sign_out'
LOGIN_REDIRECT_URL = 'home'
AUTH_USER_MODEL = 'joltem.User'
AUTH_SERVICE_USERNAMES = ['joltem']
BASE_FROM_EMAIL = 'support@joltem.com'
NOTIFY_FROM_EMAIL = BASE_FROM_EMAIL
SOLUTION_LIFE_PERIOD_SECONDS = 60 * 60 * 24 * 30
SOLUTION_REVIEW_PERIOD_SECONDS = 60 * 60 * 24 * 7
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
    'gateway',
    'git',
    'help',
    'account',
    'new_relic',
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

# Define notification types
NOTIFICATION_TYPES = lambda s: setattr(NOTIFICATION_TYPES, s, s)
NOTIFICATION_TYPES('comment_added')
NOTIFICATION_TYPES('solution_archived')
NOTIFICATION_TYPES('solution_evaluation_changed')
NOTIFICATION_TYPES('solution_marked_complete')
NOTIFICATION_TYPES('solution_posted')
NOTIFICATION_TYPES('task_accepted')
NOTIFICATION_TYPES('task_posted')
NOTIFICATION_TYPES('task_rejected')
NOTIFICATION_TYPES('vote_added')
NOTIFICATION_TYPES('vote_updated')

# Haystack settings
INSTALLED_APPS += 'haystack',
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': op.join(PROJECT_ROOT, 'whoosh_index'),
    }
}
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

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
    },
    'activity-feed': {
        'task': 'project.tasks.prepare_activity_feeds',
        'schedule': timedelta(hours=24),
        'args': (),
    },
    'archive-solution': {
        'task': 'solution.tasks.archive_solutions',
        'schedule': timedelta(hours=4),
        'args': (),
    },
    'review-solution': {
        'task': 'solution.tasks.review_solutions',
        'schedule': timedelta(hours=4),
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
        'consumer_key': 'na',
        'consumer_secret': 'na',
        'profile_url': 'http://twitter.com/{username}',
    },

    'google': {
        'id': authomatic.provider_id(),
        'class_': oauth2.Google,
        'consumer_key': 'na',
        'consumer_secret': 'na',
        'scope': ['email'],
        'profile_url': 'https://plus.google.com/u/0/{service_id}/',
    },

    'facebook': {
        'id': authomatic.provider_id(),
        'class_': oauth2.Facebook,
        'consumer_key': 'na',
        'consumer_secret': 'na',
        'scope': ['email'],
        'profile_url': 'http://facebook.com/{username}',
    },

    'github': {
        'id': authomatic.provider_id(),
        'class_': oauth2.GitHub,
        'consumer_key': 'na',
        'consumer_secret': 'na',
        'scope': ['user:email'],
        'profile_url': 'http://github.com/{username}',
        'access_headers': {'User-Agent': 'Joltem'},
    },

    'bitbucket': {
        'id': authomatic.provider_id(),
        'class_': oauth1.Bitbucket,
        'consumer_key': 'na',
        'consumer_secret': 'na',
        'profile_url': 'http://bitbucket.com/{username}',
    }

}


TEMPLATE_CONTEXT_PROCESSORS += 'settings_context_processor.context_processors.settings', # noqa
TEMPLATE_VISIBLE_SETTINGS = 'DEBUG',

logging.info("Production settings loaded.")
