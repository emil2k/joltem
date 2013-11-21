""" View related tests for core app. """
from django.test.testcases import TestCase

from joltem.libs import mixer


class HomeTest(TestCase):

    """ Test home view.

    Should just redirect to the main project page, because there is
    no other projects.

    """

    def setUp(self):
        """ Setup a project and request factory. """
        self.project = mixer.blend('project.project')

    def test_get(self):
        """ Test GET homepage request. """
        user = mixer.blend('joltem.user', password='test')
        self.client.login(username=user.username, password='test')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
