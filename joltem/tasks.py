""" Joltem related tasks. """
from __future__ import absolute_import

from celery import group
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.db.models import F
from django.template import Context
from django.template.loader import get_template

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


DAILY_TEMPLATE_HTML = 'joltem/emails/daily.html'
DAILY_TEMPLATE_TXT = 'joltem/emails/daily.txt'


@app.task(ignore_result=True)
def send_diggest_to_user(user_id):
    """ Send diggest to user.

    :return None:

    """
    from joltem.models import Notification, User, timezone

    subject = "[joltem.com] Daily diggest"

    user = User.objects.get(pk=user_id)
    notifies = Notification.objects.select_related('notifying').filter(
        user=user, is_cleared=False, time_notified__gt=user.time_notified)

    msg = _prepare_msg(
        subject, DAILY_TEMPLATE_TXT, DAILY_TEMPLATE_HTML, dict(
            user=user,
            notifies=notifies,
        ), [user.email]
    )
    msg.send()

    user.time_notified = timezone.now()
    user.save()

    return True


@app.task(ignore_result=True)
def send_immediately_to_user(notification_id):
    """ Send notification immediately. """
    from joltem.models import Notification

    notification = Notification.objects.select_related('user').get(
        pk=notification_id)

    subject = "[joltem.com] %s" % notification.type

    msg = _prepare_msg(
        subject, 'joltem/emails/immediately.txt',
        'joltem/emails/immediately.html', dict(
            user=notification.user,
            notification=notification,
        ), [notification.user.email]
    )
    msg.send()


def _prepare_msg(
        subject, txt_template, html_template, context, to_emails,
        from_email=settings.NOTIFY_FROM_EMAIL):

    context = Context(context)
    txt = get_template(txt_template).render(context)
    html = get_template(html_template).render(context)

    msg = EmailMultiAlternatives(
        subject, txt, from_email, to_emails)
    msg.attach_alternative(html, "text/html")
    return msg
