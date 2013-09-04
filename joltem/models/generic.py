import logging

from django.db import models
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger('django')


class Owned(models.Model):
    """
    Abstract, a model that has an owner
    """
    owner = None

    class Meta:
        abstract = True

    def is_owner(self, user):
        """
        Whether the passed user is person who posted the task
        """
        if self.owner is None:
            raise ImproperlyConfigured("Owner foreign key field must be set in implementing class.")
        return self.owner_id == user.id