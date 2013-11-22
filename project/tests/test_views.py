""" View related tests for project app. """

from django.test.testcases import TestCase
from joltem.libs.mock import models, requests
from joltem.libs import mixer
from django.core.urlresolvers import reverse


class BaseProjectViewTest(TestCase):

    """ Test case for view that requires a project. """

    def setUp(self):
        self.project = models.get_mock_project('bread')
        self.user = models.get_mock_user('bill')

    def _get(self, view):
        """ Get GET response on given project view.

        :param view: view to test.
        :return: HTTP response.

        """
        request = requests.get_mock_get_request(
            user=self.user, is_authenticated=True)
        return view(request, project_name=self.project.name)

    def _post(self, view, data):
        """ Get POST response on given project view.

        :param view: view to test.
        :return: HTTP response.

        """
        request = requests.get_mock_post_request(
            user=self.user, is_authenticated=True, data=data)
        return view(request, project_name=self.project.name)


class TestProjectViews(TestCase):

    def test_unknown_project(self):
        user = mixer.blend('joltem.user', password='test')
        self.client.login(username=user.username, password='test')
        uri = reverse('project:project', kwargs=dict(project_name='unknown'))
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 404)
