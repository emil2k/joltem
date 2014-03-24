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
def daily_digest():
    """ Send daily digest to users.

    :return celery.group:

    """
    from joltem.models import User
    tasks = []
    for user in set(User.objects.filter(
            can_contact=True,
            time_notified__lt=F('notification__time_notified'),
            notification__is_cleared=False,
            notify_by_email=User.NOTIFY_CHOICES.daily)):
        tasks.append(send_digest_to_user.si(user.id))

    digests = group(tasks)
    return digests.delay()


@app.task(ignore_result=True)
def send_digest_to_user(user_id):
    """ Send daily digest to user.

    :param user_id:
    :return:

    """
    from joltem.models import Notification, User, timezone
    subject = "[joltem.com] Daily digest"
    user = User.objects.get(pk=user_id)
    notifies = Notification.objects.select_related('notifying').filter(
        user=user, is_cleared=False, time_notified__gt=user.time_notified)
    msg = _prepare_msg(
        subject, 'joltem/emails/daily.txt', 'joltem/emails/daily.html', dict(
            host=settings.URL,
            user=user,
            notifies=notifies,
        ), [user.email]
    )
    msg.send()
    user.time_notified = timezone.now()
    user.save()
    return True


@app.task(ignore_result=True)
def meeting_invitation():
    """ Prepare and send invitation to initiation meeting for new members.

    An email is to all new members inviting them to a weekly Google Hangout
    where they can meet other members and get answers to any of their
    questions.

    :return:

    """
    from joltem.models import User
    tasks = []
    for user in set(User.objects.filter(
            can_contact=True,
            sent_meeting_invitation=False)):
        tasks.append(send_meeting_invitation_to_user.si(user.id))
    invitations = group(tasks)
    return invitations.delay()


@app.task(ignore_result=True)
def send_meeting_invitation_to_user(user_id):
    """ Send meeting invitation email to the user specified.

    :param user_id:
    :return:

    """
    from joltem.models import User
    subject = "Hangout Invitation"
    user = User.objects.get(pk=user_id)
    msg = _prepare_msg(
        subject,
        'joltem/emails/meeting_invitation.txt',
        'joltem/emails/meeting_invitation.html',
        dict(
            host=settings.URL,
            user=user
        ), [user.email], from_email=settings.PERSONAL_FROM_EMAIL
    )
    msg.send()
    user.sent_meeting_invitation = True
    user.save()
    return True


@app.task(ignore_result=True)
def send_immediately_to_user(notification_id):
    """ Send notification immediately. """
    from joltem.models import Notification
    notification = Notification.objects.select_related('user').get(
        pk=notification_id)
    if notification.user.can_contact:
        subject = "[joltem.com] %s" % notification.type
        msg = _prepare_msg(
            subject, 'joltem/emails/immediately.txt',
            'joltem/emails/immediately.html', dict(
                host=settings.URL,
                user=notification.user,
                notification=notification,
            ), [notification.user.email]
        )
        msg.send()


def _prepare_msg(
        subject, txt_template, html_template, context, to_emails,
        from_email=settings.NOTIFY_FROM_EMAIL):
    """ Prepare email message with HTML alternative.

    :param subject:
    :param txt_template:
    :param html_template:
    :param context:
    :param to_emails:
    :param from_email:
    :return EmailMultiAlternatives: instance of email message.

    """

    context = Context(context)
    txt = get_template(txt_template).render(context)
    html = get_template(html_template).render(context)

    msg = EmailMultiAlternatives(
        subject, txt, from_email, to_emails)
    msg.attach_alternative(html, "text/html")
    return msg
