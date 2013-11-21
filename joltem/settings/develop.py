""" Development settings. """

from .production import *


ENVIRONMENT_NAME = "dev"
URL = 'joltem.local'

# Debug
DEBUG = True
TEMPLATE_DEBUG = DEBUG
TEMPLATE_CONTEXT_PROCESSORS += 'django.core.context_processors.debug',
CHANNEL_SANDBOX = True
MIDDLEWARE_CLASSES += 'debug_toolbar.middleware.DebugToolbarMiddleware',
INSTALLED_APPS += 'debug_toolbar', 'django_extensions'
INTERNAL_IPS = '127.0.0.1'
DEBUG_TOOLBAR_CONFIG = {
    "INTERCEPT_REDIRECTS": False,
    "HIDE_DJANGO_SQL": False,
    "ENABLE_STACKTRACES": True,
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
}
DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging
LOGGING['loggers']['django.request']['level'] = 'WARNING'
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'WARNING'
}

# Caches
CACHES['default']['KEY_PREFIX'] = '_'.join((PROJECT_NAME, ENVIRONMENT_NAME))

# Let cookie to be sent via http
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Celery settings
CELERYD_CONCURRENCY = 1

AUTHOMATIC['github']['consumer_key'] = 'd98e664756592ebd11bb'
AUTHOMATIC['github']['consumer_secret'] = '5565673e92f7cfc03b9c465e2aeff0d61236da2e'
AUTHOMATIC['github']['access_headers'] = {'User-Agent', 'Joltem-local'},
AUTHOMATIC['bitbucket']['consumer_key'] = 'uNFNUZGcVjkCsBYZUW'
AUTHOMATIC['bitbucket']['consumer_secret'] = 'KketfJxxTgEJf653MATprbnaah8NKrEX'
AUTHOMATIC['facebook']['consumer_key'] = '250120505145639'
AUTHOMATIC['facebook']['consumer_secret'] = 'db1e7ea965685c7c3ee3326188cbb4b9'
AUTHOMATIC['twitter']['consumer_key'] = 'PzL35ws37R0NQ2w5ZF43A'
AUTHOMATIC['twitter']['consumer_secret'] = 'WIwpacf5c1oHpTxvVOuynN5Tf74QUKNWw7Fp5DU'

logging.info('Develop settings are loaded.')

# lint_ignore=W0614,W0401,C0301,E501
