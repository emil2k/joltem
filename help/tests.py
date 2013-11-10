""" Help section related tests. """

from django.utils import unittest
from django.test.client import RequestFactory

from help.views import HelpIndexView


class HelpIndexTest(unittest.TestCase):

    """ Test help index view behaviour. """

    def setUp(self):
        """ Setup a request factory. """
        self.factory = RequestFactory()
        self.view = HelpIndexView.as_view()

    def test_get(self):
        """ Test GET request of help index view. """
        request = self.factory.get('/help/')
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
