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
    username = models.CharField(
        max_length=200, blank=True, null="True")

    user = models.ForeignKey(User)

    def __unicode__(self):
        return u"%s (%s)" % (self.username, self.service)

    def get_profile_url(self):
        """ Return URL to user profile.

        :return str:

        """
        return settings.AUTHOMATIC[self.service]['profile_url'].format(
            **self.__dict__)
