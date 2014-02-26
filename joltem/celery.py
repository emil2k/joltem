""" Celery integration. """

from __future__ import absolute_import

import os

from celery import Celery
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'joltem.settings.local')

app = Celery('joltem')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(['joltem','project','solution','gateway'], related_name='tasks')
