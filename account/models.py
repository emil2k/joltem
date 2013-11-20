""" Account models. """

from django.db import models
from django.conf import settings

from joltem.models import User
from joltem.models.utils import Choices


class OAuth(models.Model):

    """ Save accosited OAuth credentials. """

    SERVICE_CHOICES = Choices(*settings.AUTHOMATIC.keys())

    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    service_id = models.CharField(max_length=200)
    user = models.ForeignKey(User)
