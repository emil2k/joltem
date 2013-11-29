""" View related tests for project app. """
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase
from django.core.cache import cache

from joltem.libs import mixer
from joltem.libs.mock import models, requests


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

    def setUp(self):
        self.project = mixer.blend('project.project')
        self.user = mixer.blend('joltem.user', password='test')
        self.client.login(username=self.user.username, password='test')

    def test_unknown_project(self):
        uri = reverse('project:project', kwargs=dict(project_name='unknown'))
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 404)

    def test_dashboard(self):
        uri = reverse('project:project', kwargs=dict(
            project_name=self.project.name))
        response = self.client.get(uri)
        self.assertTrue(response.context['project'])
        self.assertFalse(response.context['solutions'])
        self.assertFalse(response.context['comments'])
        self.assertFalse(response.context['tasks'])

        tasks = mixer.cycle(5).blend('task.task', project=self.project)
        solutions = mixer.cycle(5).blend(
            'solution.solution', task=(t for t in tasks),
            project=mixer.mix.task.project)
        mixer.cycle(5).blend(
            'joltem.comment', commentable=mixer.random(*solutions),
            owner=mixer.select('joltem.user'), project=self.project)

        response = self.client.get(uri)
        self.assertFalse(response.context['solutions'])
        self.assertFalse(response.context['comments'])
        self.assertFalse(response.context['tasks'])

        cache.set('project:overview:%s' % self.project.id, None)

        with self.assertNumQueries(12):
            response = self.client.get(uri)

        self.assertTrue(response.context['solutions'])
        self.assertTrue(response.context['comments'])
        self.assertTrue(response.context['tasks'])
