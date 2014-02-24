""" Classed related to custom New Relic solution. """

from django.db import models
from django.utils import timezone


class NewRelicTransferEvent(models.Model):

    """ Abstract model, for creating New Relic transfer event records.

    These events keep track of the number of bytes transferred in and out
    during each event. Periodically, they are aggregated and sent to New Relic.

    :param time_posted:
    :param duration: duration of transfer event in microseconds
    :param bytes_in:
    :param bytes_out:

    """

    time_posted = models.DateTimeField(default=timezone.now)
    duration = models.BigIntegerField(null=False, blank=False)
    bytes_in = models.BigIntegerField(null=False, blank=False)
    bytes_out = models.BigIntegerField(null=False, blank=False)

    class Meta():
        abstract = True

    def __unicode__(self):
        return u'%d in / %d out (bytes) in %d microseconds.' % (
            self.bytes_in, self.bytes_out, self.duration
        )