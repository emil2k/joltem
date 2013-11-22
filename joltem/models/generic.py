""" Joltem models mixin. """

import logging

from django.db import models
from django.core.exceptions import ValidationError

logger = logging.getLogger('django')


class Owned(models.Model):

    """ Abstract, a model that has an owner. """

    owner = None

    class Meta:
        abstract = True

    def clean(self):
        super(Owned, self).clean()

        if self.owner_id is None:
            raise ValidationError(
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

    def clean(self):
        super(ProjectContext, self).clean()

        if self.project_id is None:
            raise ValidationError(
                "Project foreign key field must be set in implementing class.")
