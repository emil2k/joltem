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

    def __init__(self, *args, **kwargs):
        if self.owner is None:
            raise ImproperlyConfigured("Owner foreign key field must be set in implementing class.")
        super(Owned, self).__init__(*args, **kwargs)

    def is_owner(self, user):
        """
        Whether the passed user is person who posted the task
        """
        return self.owner_id == user.id


class ProjectContext(models.Model):
    """
    Abstract, a model that can only be defined in some projects context
    """
    project = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        if self.project is None:
            raise ImproperlyConfigured("Project foreign key field must be set in implementing class.")
        super(ProjectContext, self).__init__(*args, **kwargs)
