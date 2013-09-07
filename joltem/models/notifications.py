import logging

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic, models as content_type_models
from django.contrib.contenttypes.generic import ContentType
from django.utils import timezone
from django.db.models.signals import post_save, post_delete

from joltem.receivers import update_notification_count

import json

logger = logging.getLogger('django')


# Notification related

class Notification(models.Model):
    """
    Notification to a user
    """
    user = models.ForeignKey(User)  # user to notify
    type = models.CharField(max_length=200, null=True, blank=True) # notification type, since each model may have multiple different notifications
    json_kwargs = models.CharField(max_length=200, null=True, blank=True) # pass to the notifying class to determine url and text of notification
    is_cleared = models.BooleanField(default=False)  # whether the notification has been clicked or marked cleared
    time_notified = models.DateTimeField(default=timezone.now)
    time_cleared = models.DateTimeField(null=True, blank=True)
    # Generic relations
    notifying_type = models.ForeignKey(content_type_models.ContentType)
    notifying_id = models.PositiveIntegerField()
    notifying = generic.GenericForeignKey('notifying_type', 'notifying_id')

    class Meta:
        app_label = "joltem"

    @property
    def kwargs(self):
        return json.loads(self.json_kwargs)

    @kwargs.setter
    def kwargs(self, kwargs):
        self.json_kwargs = json.dumps(kwargs)

    def mark_cleared(self):
        self.is_cleared = True
        self.time_cleared = timezone.now()
        self.save()


class Notifying(models.Model):
    """
    Abstract, an object that can produce notifications
    """

    class Meta:
        abstract = True

    def notify(self, user, type, update=False, kwargs={}):
        """
        Send notification to user
        """
        if not update:
            # Just create a new notification
            self.create_notification(user, type, kwargs)
        else:
            # Attempt to update the latest notifications instead of creating a new one
            notifying_type = ContentType.objects.get_for_model(self)
            notifications = Notification.objects.filter(
                user_id=user.id,
                type=type,
                notifying_type_id=notifying_type.id,
                notifying_id=self.id
            )
            if notifications.count() > 0:
                self.update_notification(notifications[0])  # update latest notification
            else:
                self.create_notification(user, type, kwargs)

    def update_notification(self, notification):
        notification.is_cleared = False
        notification.time_cleared = None
        notification.time_notified = timezone.now()
        notification.save()

    def create_notification(self, user, type, kwargs={}):
        # todo add kwargs
        notification = Notification(
            user=user,
            type=type,
            time_notified=timezone.now(),
            is_cleared=False,
            notifying=self,
            kwargs=kwargs
        )
        notification.save()

    def delete_notifications(self, user, type):
        """
        Delete all notifications of this type from this notifying to this user
        """
        notifying_type = ContentType.objects.get_for_model(self)
        notifications = Notification.objects.filter(
            user_id=user.id,
            type=type,
            notifying_type_id=notifying_type.id,
            notifying_id=self.id
        )
        for notification in notifications:
            notification.delete()

    def get_notification_text(self, notification):
        """
        Get notification text for a given notification
        """
        raise ImproperlyConfigured("Extending class must implement get notification text.")

    def get_notification_url(self, notification):
        """
        Get notification url for a given notification, implementation should use reverse
        and should not hard code urls
        """
        raise ImproperlyConfigured("Extending class must implement get notification url.")


post_save.connect(update_notification_count, sender=Notification)
post_delete.connect(update_notification_count, sender=Notification)