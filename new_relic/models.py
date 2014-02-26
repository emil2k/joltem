""" Classed related to custom New Relic solution. """
import json
import requests
from django.conf import settings
from django.db import models
from django.utils import timezone


class NewRelicReport(models.Model):

    """ Generate and keeps track of reports sent to New Relic.

    :param time_reported: when the report was sent.
    :param duration: in seconds, what span the report covered.
    :is_recorded: whether the report was successful, recorded at New Relic.
        meaning status code was 200
    :status_code: the status code of the response, keep for record if failed.

    :param component_guid: A "reverse domain name" styled identifier; for
        example, com.newrelic.mysql. This is a unique identity defined in the
        plugin's user interface, which ties the agent data to the
        corresponding plugin user interface in New Relic.
    :param event_classes: The classes of New Relic events to compile into
        report.

    """

    AGENT_HOST = settings.GATEWAY_HOST
    AGENT_VERSION = '0.1.0'

    time_reported = models.DateTimeField(default=timezone.now)
    duration = models.IntegerField(null=False, blank=False)
    is_recorded = models.BooleanField(default=False)
    status_code = models.IntegerField(null=False, blank=False)

    # Component related

    component_guid = None
    event_classes = ()

    class Meta():
        abstract = True

    def get_report(self):
        """ Compile the `report` hash for the report.

        :return dict:

        """
        return dict(
            agent=self.get_agent(),
            components=[self.get_component(self.AGENT_HOST)]
        )

    @classmethod
    def get_duration(cls):
        """ Get duration of next report.

        Looks for previous reports, in sequence, that it can retry.

        :param cls:
        :return int: duration in seconds of next report.

        """
        duration = settings.NEW_RELIC_REPORT_DURATION
        try:
            r = cls.objects.order_by('-time_reported').get()
        except cls.DoesNotExist:
            pass
        else:
            if not r.is_recorded and r.status_code >= 500:
                duration += r.duration
        return duration

    def send_report(self):
        """ Attempt to send report to New Relic. """
        url = 'http://platform-api.newrelic.com/platform/v1/metrics'
        headers = {
            'X-License-Key': settings.NEW_RELIC_LICENSE_KEY,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.process_response(
            requests.post(
                url, data=json.dumps(self.get_report()), headers=headers))

    def process_response(self, response):
        """ Process response from sending report.

        :param response: `Response` instance

        """
        self.status_code = response.status_code
        if self.status_code == requests.codes.ok:
            self.is_recorded = True
            self.flush_old()
        self.save()

    def flush_old(self):
        """ Deleted all records older then time_reported.

        There is no reason to keep records after a successful report.

        """
        for cls in self.event_classes:
            cls.objects.filter(time_posted__lte=self.time_reported).delete()

    @classmethod
    def get_agent(cls):
        """ Compile the `agent` hash for the report.

        :return dict:

        """
        return dict(
            host=cls.AGENT_HOST,
            version=cls.AGENT_VERSION
        )

    def get_component(self, host):
        """ Compile the `component` hash for the report.

        :param host: agent host
        :return dict:

        """
        return dict(
            name=host,
            guid=self.component_guid,
            duration=self.duration,
            metrics=self.get_metrics(),
        )

    def get_metrics(self):
        """ Compile teh `metrics` hash for the report.

        Combine the metrics from all the event classes in the hash.

        :return dict: metric names => metrics

        """
        metrics = {}
        frontier = self.time_reported - timezone.timedelta(
            seconds=self.duration)
        for e in self.event_classes:
            metrics.update(e.get_metrics(e.objects.filter(
                time_posted__gte=frontier)))
        return metrics


class NewRelicTransferEvent(models.Model):

    """ Abstract model, for creating New Relic transfer event records.

    These events keep track of the number of bytes transferred in and out
    during each event. Periodically, they are aggregated and sent to New Relic.

    :param time_posted:
    :param duration: duration of transfer event in microseconds
    :param bytes_in:
    :param bytes_out:

    According to New Relic metric naming convention :
    https://docs.newrelic.com/docs/plugin-dev/metric-naming-reference

    :param metric_name_prefix:
    :param metric_name_transfer_type:

    """

    time_posted = models.DateTimeField(default=timezone.now)
    duration = models.BigIntegerField(null=False, blank=False)
    bytes_in = models.BigIntegerField(null=False, blank=False)
    bytes_out = models.BigIntegerField(null=False, blank=False)

    metric_name_prefix = 'Component'
    metric_name_transfer_type = None

    class Meta():
        abstract = True

    def __unicode__(self):
        return u'%d in / %d out (bytes) at %d Bps.' % (
            self.bytes_in, self.bytes_out, self.bit_rate
        )

    @classmethod
    def get_metrics(cls, qs):
        """ Compile the `metric` hash that can be placed in a report.

        :return qs: queryset over which to compile metrics.
        :return dict: metric names => metrics

        """
        return {
            cls.metric_name_bytes_in(): cls.get_bytes_in_metrics(qs),
            cls.metric_name_bytes_out(): cls.get_bytes_out_metrics(qs),
            cls.metric_name_bytes_total(): cls.get_bytes_total_metrics(qs),
            cls.metric_name_bit_rate(): cls.get_bit_rate_metrics(qs),
        }

    @classmethod
    def get_bytes_in_metrics(cls, qs):
        """ Return bytes in metrics for reporting to New Relic.

        :param qs: queryset of transfer events.
        :return dict:

        """
        return cls._get_metrics(qs, lambda e: e.bytes_in)

    @classmethod
    def metric_name_bytes_in(cls):
        """ Metric name for bytes in.

        :return str:

        """
        return cls._get_metric_name("Bytes In", "bytes")

    @classmethod
    def get_bytes_out_metrics(cls, qs):
        """ Return bytes out metrics for reporting to New Relic.

        :param qs: queryset of transfer events.
        :return dict:

        """
        return cls._get_metrics(qs, lambda e: e.bytes_out)

    @classmethod
    def metric_name_bytes_out(cls):
        """ Metric name for bytes out.

        :return str:

        """
        return cls._get_metric_name("Bytes Out", "bytes")

    @property
    def bit_rate(self):
        """ Bit rate is expressed in Bps ( bytes per second ).

        :return int: Bps

        """
        b = self.bytes_in + self.bytes_out
        return int(b * 1000000 / float(self.duration))

    @classmethod
    def get_bit_rate_metrics(cls, qs):
        """ Return bit rate metrics for reporting to New Relic.

        Bit rate is expressed in Bps ( bytes per second ).

        :param qs: queryset of transfer events.
        :return dict:

        """
        return cls._get_metrics(qs, lambda e: e.bit_rate)

    @classmethod
    def metric_name_bit_rate(cls):
        """ Metric name for bit rate.

        :return str:

        """
        return cls._get_metric_name("Bit Rate", "bytes/second")

    @classmethod
    def get_bytes_total_metrics(cls, qs):
        """ Return bytes total metrics for reporting to New Relic.

        :param qs: queryset of transfer events.
        :return dict:

        """
        return cls._get_metrics(qs, lambda e: e.bytes_in + e.bytes_out)

    @classmethod
    def metric_name_bytes_total(cls):
        """ Metric name for bytes total.

        :return str:

        """
        return cls._get_metric_name("Bytes Total", "bytes")

    @classmethod
    def _get_metric_name(cls, label, units):
        """ Get metric name for reporting to New Relic.

        :param label: an identifier of the metric
        :param units: the units for the metric. i.e. bytes/second
        :return str: metric name

        """
        return "%s/%s/%s[%s]" % (
            cls.metric_name_prefix,
            cls.metric_name_transfer_type,
            label,
            units
        )

    @classmethod
    def _get_metrics(cls, qs, fmap):
        """ Return metrics for reporting to New Relic.

        :param qs: queryset of transfer events.
        :param fmap: function to map event to value.
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
            value = fmap(e)
            metrics['total'] += value
            metrics['count'] += 1
            if value < metrics['min'] or metrics['min'] is None:
                metrics['min'] = value
            if value > metrics['max'] or metrics['max'] is None:
                metrics['max'] = value
            metrics['sum_of_squares'] += pow(value, 2)
        return metrics


if settings.ENVIRONMENT_NAME == 'test':

    class MockTransferEvent(NewRelicTransferEvent):

        """ A mock transfer event to test the abstract class. """

        metric_name_transfer_type = 'Receive'

        class Meta:
            app_label = 'new_relic'

    class MockTransferUploadEvent(NewRelicTransferEvent):

        """ A mock upload transfer event to test the abstract report class. """

        metric_name_transfer_type = 'Upload'

        class Meta:
            app_label = 'new_relic'

    class MockReport(NewRelicReport):

        """ A mock report to test the abstract class. """

        AGENT_HOST = 'stage.joltem.local'

        component_name = "Git Server"
        component_guid = "com.joltem.git"

        event_classes = (MockTransferEvent, )

        class Meta:
            app_label = 'new_relic'

    class MockReportBoth(NewRelicReport):

        """ A mock report to test the abstract class. """

        AGENT_HOST = 'stage.joltem.local'

        component_name = "Git Server"
        component_guid = "com.joltem.git"

        event_classes = (MockTransferEvent, MockTransferUploadEvent)

        class Meta:
            app_label = 'new_relic'
