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

    @classmethod
    def get_bytes_in_metrics(cls, qs):
        """ Returns bytes in metrics for reporting to New Relic.

        :param qs: queryset of transfer events.
        :return dict:

        """
        return cls._get_metrics(qs, lambda e: e.bytes_in)

    @classmethod
    def get_bytes_out_metrics(cls, qs):
        """ Returns bytes out metrics for reporting to New Relic.

        :param qs: queryset of transfer events.
        :return dict:

        """
        return cls._get_metrics(qs, lambda e: e.bytes_out)

    @property
    def bit_rate(self):
        """ Bit rate is expressed in Bps ( bytes per second ).

        :return int: Bps

        """
        bytes = self.bytes_in + self.bytes_out
        return int(bytes*1000000/float(self.duration))

    @classmethod
    def get_bit_rate_metrics(cls, qs):
        """ Returns bit rate metrics for reporting to New Relic.

        Bit rate is expressed in Bps ( bytes per second ).

        :param qs: queryset of transfer events.
        :return dict:

        """
        return cls._get_metrics(qs, lambda e: e.bit_rate)


    @classmethod
    def _get_metrics(cls, qs, map):
        """ Returns metrics for reporting to New Relic.

        :param qs: queryset of transfer events.
        :param map: function to map event to value.
        :return dict:

        """
        metrics = dict(
            total=0,
            count=0,
            min=None,
            max=None,
            sum_of_squares=0
        )
        for e in qs:
            value = map(e)
            metrics['total'] += value
            metrics['count'] += 1
            if value < metrics['min'] or metrics['min'] is None:
                metrics['min'] = value
            if value > metrics['max'] or metrics['max'] is None:
                metrics['max'] = value
            metrics['sum_of_squares'] += pow(value, 2)
        return metrics
