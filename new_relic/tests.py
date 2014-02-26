""" New Relic related tests. """
from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from .models import (
    MockTransferEvent, MockTransferUploadEvent, MockReportBoth, MockReport)
from joltem.libs import mixer, load_model


class TransferEventTest(TestCase):

    """ Test New Relic transfer events. """

    def test_mock(self):
        """ Test that mock transfer object works. """
        e = mixer.blend(MockTransferEvent, bytes_in=100, bytes_out=100,
                        duration=100000)
        self.assertEqual(load_model(e).__class__.__name__, 'MockTransferEvent')

    def test_bit_rate(self):
        """ Test Bps calculation. """
        e = mixer.blend(MockTransferEvent, bytes_in=5244906, bytes_out=176,
                        duration=254372)
        self.assertEqual(e.bit_rate, 20619730)

    def test_metric_name(self):
        """ Test metric names. """
        self.assertEqual(
            MockTransferEvent.metric_name_bit_rate(),
            "Component/Receive/Bit Rate[bytes/second]")
        self.assertEqual(
            MockTransferEvent.metric_name_bytes_total(),
            "Component/Receive/Bytes Total[bytes]")
        self.assertEqual(
            MockTransferEvent.metric_name_bytes_in(),
            "Component/Receive/Bytes In[bytes]")
        self.assertEqual(
            MockTransferEvent.metric_name_bytes_out(),
            "Component/Receive/Bytes Out[bytes]")

    def test_metrics(self):
        """ Test calculation of metrics.

        :return:

        """
        cls = MockTransferEvent
        mixer.cycle(3).blend(
            cls,
            bytes_in=mixer.sequence(5, 1, 4000 * 4000),
            bytes_out=mixer.sequence(7, 8, 100),
            duration=mixer.sequence(8, 9, 5000)
        )
        self.assertDictEqual(
            cls.get_bytes_in_metrics(cls.objects.all()),
            dict(
                total=4000 * 4000 + 6,
                count=3,
                min=1,
                max=4000 * 4000,
                sum_of_squares=25 + 1 + pow(4000 * 4000, 2)
            )
        )
        self.assertDictEqual(
            cls.get_bytes_out_metrics(cls.objects.all()),
            dict(
                total=7 + 8 + 100,
                count=3,
                min=7,
                max=100,
                sum_of_squares=49 + 64 + 100 * 100
            )
        )


class ReportTest(TestCase):

    """ Test New Relic report. """

    def test_metrics_combining(self):
        """ Test whether metrics combining properly into one hash. """
        mixer.cycle(3).blend(MockTransferEvent)
        mixer.cycle(3).blend(MockTransferUploadEvent)
        report = MockReportBoth(duration=30)
        self.assertEqual(len(report.get_metrics().items()), 8)

    def test_metrics_frontier(self):
        """ Test whether abides by time frontier set by duration. """
        NOW = timezone.now()
        OLD = NOW - timezone.timedelta(seconds=31)
        mixer.cycle(3).blend(MockTransferEvent, time_posted=NOW)
        mixer.cycle(3).blend(MockTransferEvent, time_posted=OLD)
        report = MockReport(duration=30)
        count = lambda x: x['count']
        for _, v in report.get_metrics().items():
            self.assertEqual(count(v), 3)

    def test_duration_5XX(self):
        """ Test getting duration for next report after a 5XX. """
        self.assertEqual(MockReport.get_duration(),
                         settings.NEW_RELIC_REPORT_DURATION)
        mixer.blend(MockReport, status_code=537, duration=90)
        self.assertEqual(MockReport.get_duration(),
                         settings.NEW_RELIC_REPORT_DURATION + 90)

    def test_duration_4XX(self):
        """ Test getting duration for next report after a 4XX. """
        self.assertEqual(MockReport.get_duration(),
                         settings.NEW_RELIC_REPORT_DURATION)
        mixer.blend(MockReport, status_code=424, duration=90)
        self.assertEqual(MockReport.get_duration(),
                         settings.NEW_RELIC_REPORT_DURATION)

    def test_flush_old(self):
        """ Test flushing old entries. """
        NOW = timezone.now()
        NEW = NOW + timezone.timedelta(seconds=1)
        OLD = NOW - timezone.timedelta(seconds=1)
        mixer.cycle(5).blend(MockTransferEvent,
                             time_posted=mixer.sequence(OLD, NOW, NEW))
        mixer.cycle(5).blend(MockTransferUploadEvent,
                             time_posted=mixer.sequence(OLD, NOW, NEW))
        r = MockReportBoth(duration=30, time_reported=NOW)
        r.flush_old()
        self.assertEqual(MockTransferEvent.objects.count(), 1)
        self.assertEqual(MockTransferUploadEvent.objects.count(), 1)
