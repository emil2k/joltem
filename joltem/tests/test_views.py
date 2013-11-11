""" View related tests for core app. """

from django.utils.unittest import TestCase
from django.test.client import RequestFactory

from joltem.views import home
from joltem.libs.mock.models import get_mock_project
from joltem.libs.mock.requests import mock_authentication_middleware

class HomeTest(TestCase):

    """ Test home view.

    Should just redirect to the main project page, because there is
    no other projects.

    """

    def setUp(self):
        """ Setup a project and request factory. """
        self.factory = RequestFactory()
        self.project = get_mock_project('main')
        self.view = home

    def test_get(self):
        """ Test GET homepage request. """
        request = mock_authentication_middleware(self.factory.get('/'))
        request.user._is_authenticated = True
        response = self.view(request)
        self.assertEqual(response.status_code, 302)


