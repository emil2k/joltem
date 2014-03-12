""" Stage's settings. """

from .production import *


ENVIRONMENT_NAME = 'stage'

# Disable emails on stage
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

logging.info("Stage settings are loaded.")
