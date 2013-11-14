""" Joltem models mixin. """

import logging

from django.db import models
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger('django')


class Owned(models.Model):

    """ Abstract, a model that has an owner. """

    owner = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(Owned, self).__init__(*args, **kwargs)
        if self.owner_id is None:
            raise ImproperlyConfigured(
                "Owner foreign key field must be set in implementing class.")

    def is_owner(self, user):
        """ Whether the passed user is person who posted the task.

        :return bool:

        """
        return self.owner_id == user.id


class ProjectContext(models.Model):

    """ Abstract, model that can only be defined in some projects context. """

    project = None

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super(ProjectContext, self).__init__(*args, **kwargs)
        if self.project_id is None:
            raise ImproperlyConfigured(
                "Project foreign key field must be set in implementing class.")
