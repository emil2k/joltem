import hashlib
import logging
from django.contrib.auth.models import AbstractUser
from django.db import models

from .notifications import Notification, Notifying  # noqa
from .votes import Vote, Voteable  # noqa
from .comments import Comment, Commentable  # noqa
from .utils import Choices


logger = logging.getLogger('django')


class User(AbstractUser):

    """ Implement Joltem User functionality. """

    NOTIFY_CHOICES = Choices(
        (0, "disable"),
        (10, "immediatly"),
        (20, "daily", "daily digest"),
    )

    gravatar_email = models.CharField(max_length=200, null=True, blank=True)
    gravatar_hash = models.CharField(max_length=200, null=True, blank=True)
    impact = models.BigIntegerField(default=0)
    completed = models.IntegerField(default=0)
    notifications = models.IntegerField(default=0)
    notify_by_email = models.PositiveSmallIntegerField(
        default=NOTIFY_CHOICES.disable, choices=NOTIFY_CHOICES)

    def update(self):
        """ Update user stats.
        """
        self.impact = self.get_impact()
        self.completed = self.get_completed()
        return self  # to chain calls

    def get_impact(self):
        impact = 0
        for project_impact in self.impact_set.all():
            if project_impact and project_impact.impact:
                impact += project_impact.impact
        return impact

    def get_completed(self):
        return self.solution_set.filter(is_completed=True).count()

    def set_gravatar_email(self, gravatar_email):
        """
        Set gravatar email and hash, checks if changed from old
        return boolean whether changed value or not
        """
        if self.gravatar_email != gravatar_email:
            self.gravatar_email = gravatar_email
            self.gravatar_hash = hashlib.md5(gravatar_email).hexdigest()
            return True
        return False
