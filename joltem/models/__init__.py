import hashlib
import logging
from django.contrib.auth.models import AbstractUser
from django.db import models

from joltem.models.notifications import Notification, Notifying  # noqa
from joltem.models.votes import Vote, Voteable  # noqa
from joltem.models.comments import Comment, Commentable  # noqa


logger = logging.getLogger('django')


class User(AbstractUser):

    """ Implement Joltem User functionality. """

    gravatar_email = models.CharField(max_length=200, null=True, blank=True)
    gravatar_hash = models.CharField(max_length=200, null=True, blank=True)
    impact = models.BigIntegerField(default=0)
    completed = models.IntegerField(default=0)
    notifications = models.IntegerField(default=0)

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
