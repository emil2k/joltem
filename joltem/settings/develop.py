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

logging.info('Develop settings are loaded.')

# lint_ignore=W0614,W0401,C0301,E501
