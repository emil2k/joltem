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
        self.project = mixer.blend('project.project', subscriber_set=[])
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

        comments = mixer.cycle(2).blend(
            'joltem.comment', commentable=mixer.random(*tasks),
            owner=mixer.select('joltem.user'), project=self.project)

        comments = mixer.cycle(3).blend(
            'joltem.comment', commentable=mixer.random(*solutions),
            owner=mixer.select('joltem.user'), project=self.project)

        response = self.client.get(uri)
        self.assertFalse(response.context['solutions'])
        self.assertFalse(response.context['comments'])
        self.assertFalse(response.context['tasks'])

        cache.set('project:overview:%s' % self.project.id, None)

        # with self.assertNumQueries(17):
            # response = self.client.get(uri)
        response = self.client.get(uri)

        self.assertTrue(response.context['solutions'])
        self.assertTrue(response.context['comments'])
        self.assertTrue(response.context['tasks'])

        solution = comments[0].commentable
        self.assertContains(response, 'commented solution "%s"' % solution.default_title)


class TestProjectSettingsView(TestCase):

    """ Test project settings view. """

    def setUp(self):
        self.project = mixer.blend('project.project')
        self.user = mixer.blend('joltem.user', password='test')
        self.uri = reverse('project:settings',
                           kwargs=dict(project_name=self.project.name))

    def _test_get(self, expected_code):
        """ Test generator for GETing project settings page.

        :param expected_code: expected response code.

        """
        response = self.client.get(self.uri)
        self.assertEqual(response.status_code, expected_code)

    def test_get_admin(self):
        """ Test GET with admin. """
        self.project.admin_set.add(self.user)
        self.project.save()
        self.client.login(username=self.user.username, password='test')
        self._test_get(200)

    def test_get_manager(self):
        """ Test GET with manager. """
        self.project.manager_set.add(self.user)
        self.project.save()
        self.client.login(username=self.user.username, password='test')
        self._test_get(404)

    def test_get_developer(self):
        """ Test GET with developer. """
        self.project.developer_set.add(self.user)
        self.project.save()
        self.client.login(username=self.user.username, password='test')
        self._test_get(404)

    def test_get_regular(self):
        """ Test GET with regular user. """
        self.client.login(username=self.user.username, password='test')
        self._test_get(404)

    def test_get_anonymous(self):
        """ Test GET with anonymous user. """
        self._test_get(302)

    def test_subscribe(self):
        self.assertFalse(self.user in self.project.subscriber_set.all())

        uri = reverse('project:project', kwargs=dict(
            project_name=self.project.name))

        self.client.login(username=self.user.username, password='test')

        self.client.post(uri, data=dict(subscribe=''))
        self.assertFalse(self.user in self.project.subscriber_set.all())

        self.client.post(uri, data=dict(subscribe='true'))
        self.assertTrue(self.user in self.project.subscriber_set.all())

        self.client.post(uri, data=dict(subscribe=''))
        self.assertFalse(self.user in self.project.subscriber_set.all())


class TestProjectSearch(TestCase):

    """ Test project search view. """

    def setUp(self):
        self.project = mixer.blend('project.project')
        self.user = mixer.blend('joltem.user', password='test')
        self.uri = reverse(
            'project:search', kwargs=dict(project_name=self.project.name))

    def test_search(self):
        mixer.blend('task.task', description='hello world')
        self.client.login(username=self.user.username, password='test')
        response = self.client.get(self.uri, data=dict(q='hello'))
        self.assertContains(response, 'search')
