""" Classed related to custom New Relic solution. """

from django.db import models
from django.utils import timezone


class NewRelicTransferEvent(models.Model):

    """ Abstract model, for creating New Relic transfer event records.

    These events keep track of the number of bytes transferred in and out
    during each event. Periodically, they are aggregated and sent to New Relic.

    :param time_posted:
    :param bytes_in:
    :param bytes_out:

    """

    time_posted = models.DateTimeField(default=timezone.now)
    bytes_in = models.BigIntegerField(null=False, blank=False)
    bytes_out = models.BigIntegerField(null=False, blank=False)

    class Meta():
        abstract = True