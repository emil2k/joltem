#!/usr/bin/env python

""" Setup uwsgi application. """

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'joltem.settings.local')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

NEW_RELIC_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'configuration', 'newrelic.ini')

if os.path.exists(NEW_RELIC_CONFIG_FILE):
    import newrelic.agent
    newrelic.agent.initialize(NEW_RELIC_CONFIG_FILE)
    application = newrelic.agent.WSGIApplicationWrapper(application)

from django.conf import settings
if settings.DEBUG:
    from werkzeug.debug import DebuggedApplication
    from django.views import debug

    def null_technical_500_response(request, exc_type, exc_value, tb):
        raise exc_type, exc_value, tb
    debug.technical_500_response = null_technical_500_response
    application = DebuggedApplication(application, evalex=True)
