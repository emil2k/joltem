""" Joltem notification support. """

import logging

from django.db import models
from django.db.models.query import QuerySet
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.contrib.contenttypes import generic, models as content_type_models
from django.contrib.contenttypes.generic import ContentType
from model_utils.managers import PassThroughManager
from django.utils import timezone
from django.db.models.signals import post_save, post_delete

from joltem.receivers import (
    update_notification_count, immediately_senf_email_about_notification)

from joltem.tasks import send_immediately_to_user

import json

logger = logging.getLogger('django')


class NotificationQuerySet(QuerySet):

    """ Operations with notifications. """

    def mark_cleared(self):
        """ Mark self query as cleared.

        :return Notification:

        """
        notifications = list(self.select_related('user'))
        self.update(is_cleared=True, time_cleared=timezone.now())
        for user in set(n.user for n in notifications):
            user.notifications = user.notification_set.filter(
                is_cleared=False).count()
            user.save()
        return self


class Notification(models.Model):

    """ Notification to a user. """

    user = models.ForeignKey(settings.AUTH_USER_MODEL)  # user to notify
    # notification type, since each model may have
    # multiple different notifications
    type = models.CharField(max_length=200, null=True, blank=True)
    # pass to the notifying class to determine
    # url and text of notification
    json_kwargs = models.CharField(max_length=200, null=True, blank=True)
    # whether the notification has been clicked or marked cleared
    is_cleared = models.BooleanField(default=False)
    time_notified = models.DateTimeField(default=timezone.now)
    time_cleared = models.DateTimeField(null=True, blank=True)
    # Generic relations
    notifying_type = models.ForeignKey(content_type_models.ContentType)
    notifying_id = models.PositiveIntegerField()
    notifying = generic.GenericForeignKey('notifying_type', 'notifying_id')

    objects = PassThroughManager.for_queryset_class(NotificationQuerySet)()

    class Meta:
        app_label = "joltem"

    def __unicode__(self):
        return u"%s%s [%s]" % (
            self.type, self.is_cleared and '-' or '+', self.user.username)

    @property
    def kwargs(self):
        """ TODO: change to JSON field.

        :return return:

        """
        return json.loads(self.json_kwargs)

    @kwargs.setter
    def kwargs(self, kwargs):
        """ TODO: change to JSON field.

        :return return:

        """
        self.json_kwargs = json.dumps(kwargs)

    def mark_cleared(self):
        """ Mark notification as cleared.

        :return Notification:

        """
        [n] = type(self).objects.filter(pk=self.pk).mark_cleared()
        self.is_cleared = n.is_cleared
        self.time_cleared = n.time_cleared
        return self

    def send_mail(self):
        """ Send email to self.user.

        :return Task:

        """
        return send_immediately_to_user.delay(self.pk)

    def get_text(self):
        """ Get notification text.

        :return str:

        """
        return self.notifying.get_notification_text(self)


class Notifying(models.Model):

    """ Abstract, an object that can produce notifications. """

    class Meta:
        abstract = True

    def notify(self, user, ntype, update=False, kwargs=None):
        """ Send notification to user.

        :param user: user to notify.
        :param ntype: a string that identifies the notification type.
        :param update: whether to replace previous notification of the same
            type or create a new notification.
        :param kwargs: extra options to pass for rending the notification.

        """
        if kwargs is None:
            kwargs = {}

        if not update:
            # Just create a new notification
            self.create_notification(user, ntype, kwargs)

        else:
            # Attempt to update the latest notifications instead of creating
            # a new one
            notifying_type = ContentType.objects.get_for_model(self)
            notifications = Notification.objects.filter(
                user_id=user.id,
                type=ntype,
                notifying_type_id=notifying_type.id,
                notifying_id=self.id
            )

            if notifications.count() > 0:
                # update latest notification
                self.update_notification(notifications[0])

            else:
                self.create_notification(user, ntype, kwargs)

    @staticmethod
    def update_notification(notification):
        """ Update notification. """

        notification.is_cleared = False
        notification.time_cleared = None
        notification.time_notified = timezone.now()
        notification.save()

    def create_notification(self, user, ntype, kwargs=None):
        """ Create notification. Why Im exists?.  """
        if kwargs is None:
            kwargs = {}
        # todo add kwargs
        notification = Notification(
            user=user,
            type=ntype,
            time_notified=timezone.now(),
            is_cleared=False,
            notifying=self,
            kwargs=kwargs
        )
        notification.save()

    def delete_notifications(self, user, ntype):
        """ Delete all notifications of this type from this notifying to this user. """ # noqa
        notifying_type = ContentType.objects.get_for_model(self)
        Notification.objects.filter(
            user_id=user.id,
            type=ntype,
            notifying_type_id=notifying_type.id,
            notifying_id=self.id
        ).delete()

    @staticmethod
    def get_notification_text(notification):
        """ Get notification text for a given notification. """

        raise ImproperlyConfigured(
            "Extending class must implement get notification text.")

    @staticmethod
    def get_notification_url(notification):
        """ Get notification url for a given notification.

        Implementation should use reverse and should not hard code urls.

        """
        raise ImproperlyConfigured(
            "Extending class must implement get notification url.")


post_save.connect(update_notification_count, sender=Notification)
post_save.connect(
    immediately_senf_email_about_notification, sender=Notification)
post_delete.connect(update_notification_count, sender=Notification)
