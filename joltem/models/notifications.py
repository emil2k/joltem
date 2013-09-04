import logging

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic, models as content_type_models
from django.utils import timezone

logger = logging.getLogger('django')


# Notification related

class Notification(models.Model):
    """
    Notification to a user
    """
    user = models.ForeignKey(User)  # user to notify
    notifying_kwargs = models.CharField(max_length=200, null=True, blank=True) # pass to the notifying class to determine url and text of notification
    is_cleared = models.BooleanField(default=False)  # whether the notification has been clicked or marked cleared
    time_notified = models.DateTimeField(default=timezone.now)
    time_cleared = models.DateTimeField(null=True, blank=True)
    # Generic relations
    notifying_type = models.ForeignKey(content_type_models.ContentType)
    notifying_id = models.PositiveIntegerField()
    notifying = generic.GenericForeignKey('notifying_type', 'notifying_id')

    class Meta:
        app_label = "joltem"

class Notifying(models.Model):
    """
    Abstract, an object that can produce notifications
    """

    class Meta:
        abstract = True

    def notify(self, user):
        """
        Send notification to user
        """
        # todo add kwargs
        notification = Notification(
            user=user,
            time_notified=timezone.now(),
            is_cleared=False,
            notifying=self
        )
        notification.save()

    def broadcast(self, users):
        """
        Broadcast a notification to a list of users
        """
        for user in users:
            self.notify(user)

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
