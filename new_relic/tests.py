""" New Relic related tests. """

from django.test import TestCase

from joltem.libs import mixer, load_model
from .models import NewRelicTransferEvent


class MockTransferEvent(NewRelicTransferEvent):

    """ A mock transfer event to test the abstract class. """

    class Meta:
        app_label = 'new_relic'


class TransferEventTest(TestCase):

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

    def test_metrics(self):
        """ Test calculation of metrics.

        :return:

        """
        cls = MockTransferEvent
        mixer.cycle(3).blend(
            cls,
            bytes_in=mixer.sequence(5,1,4000*4000),
            bytes_out=mixer.sequence(7,8,100),
            duration=mixer.sequence(8,9,5000)
        )
        self.assertDictEqual(
            cls.get_bytes_in_metrics(cls.objects.all()),
            dict(
                total=4000*4000+6,
                count=3,
                min=1,
                max=4000*4000,
                sum_of_squares=25+1+pow(4000*4000,2)
            )
        )
        self.assertDictEqual(
            cls.get_bytes_out_metrics(cls.objects.all()),
            dict(
                total=7+8+100,
                count=3,
                min=7,
                max=100,
                sum_of_squares=49+64+100*100
            )
        )