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

    def save(self, **kwargs):
        """ Check owner exists.

        :return object:

        """
        if self.owner_id is None:
            raise ImproperlyConfigured(
                "Owner foreign key field must be set in implementing class.")
        return super(Owned, self).save(**kwargs)

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

    def save(self, **kwargs):
        """ Check self.project exists.

        :return object:

        """
        if self.project_id is None:
            raise ImproperlyConfigured(
                "Project foreign key field must be set in implementing class.")
        super(ProjectContext, self).save(**kwargs)


class Updatable(models.Model):

    """ Store updated time. """

    time_updated = models.DateTimeField(auto_now=True)

    class Meta():
        abstract = True
