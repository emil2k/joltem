""" Joltem related tasks. """

from __future__ import absolute_import

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F

from celery import group

from .celery import app


@app.task(ignore_result=True)
def send_async_email(message, recipient_list, subject="Joltem"):
    """ Send email asynchronously. """

    send_mail(subject, message, settings.NOTIFY_FROM_EMAIL, recipient_list)


@app.task(ignore_result=True)
def daily_diggest():
    """ Send daily diggest to users.

    :return celery.group:

    """
    from joltem.models import User

    tasks = []
    for user in set(User.objects.filter(
            time_notified__lt=F('notification__time_notified'),
            notification__is_cleared=False,
            notify_by_email=User.NOTIFY_CHOICES.daily)):
        tasks.append(send_diggest_to_user.si(user.id))

    diggests = group(tasks)
    return diggests.delay()


@app.task(ignore_result=True)
def send_diggest_to_user(user_id):
    """ Send diggest to user.

    :return None:

    """
    from joltem.models import Notification, User, timezone

    subject = "[joltem.com] Daily diggest"
    message = ""

    user = User.objects.get(pk=user_id)
    message = "\n\n".join(
        notify.notifying.get_notification_text(notify)
        for notify in
        Notification.objects.select_related('notifying').filter(
            user=user, is_cleared=False, time_notified__gt=user.time_notified))

    send_mail(subject, message, settings.NOTIFY_FROM_EMAIL, [user.email])
    user.time_notified = timezone.now()
    user.save()
    return True
