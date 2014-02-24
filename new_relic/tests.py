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

