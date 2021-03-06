""" Settings for tests running. """

from .production import *


ENVIRONMENT_NAME = "test"
URL = 'joltem.local'

# Databases
DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
DATABASES['default']['NAME'] = ':memory:'

# Caches
CACHES['default']['BACKEND'] = 'joltem.cache.MockCacheClient'
CACHES['default']['KEY_PREFIX'] = '_'.join((PROJECT_NAME, ENVIRONMENT_NAME))

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# Disable south migrations on db creation in tests
SOUTH_TESTS_MIGRATE = False

# Nosetests
INSTALLED_APPS += 'django_nose',
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Celery
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

# Haystack
HAYSTACK_CONNECTIONS['default']['PATH'] = '/tmp/whoosh'

logging.info("Test settings loaded.")
