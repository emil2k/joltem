""" Joltem related tasks. """

from __future__ import absolute_import

from django.conf import settings
from django.core.mail import send_mail

from .celery import app


@app.task(ignore_result=True)
def send_async_email(message, recipient_list, subject="Joltem"):
    """ Send email asynchronously. """

    send_mail(subject, message, settings.NOTIFY_FROM_EMAIL, recipient_list)
