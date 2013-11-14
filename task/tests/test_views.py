""" View related tests for task app. """

from django.test.testcases import TestCase
from joltem.libs.mock import models, requests
from task import views


class TaskViewsTest(TestCase):

    """ Test task view's requests. """

    def setUp(self):
        """ Setup user, project, and task. """
        self.project = models.get_mock_project("bread")
        # Extend this class and replace task and user to test state variations
        self.user = models.get_mock_user('bill')
        self.task = models.get_mock_task(self.project, self.user)

    # Tests

    def _get_test_view(self, view):
        """ Get GET response on given task view.

        :param view: view to test.
        :return: HTTP response.

        """
        request = requests.get_mock_get_request(
            user=self.user, is_authenticated=True)
        return view(request, project_name=self.project.name,
                        task_id=self.task.id)

    def _post_test_view(self, view, data):
        """ Get POST response on given task view.

        :param view: view to test.
        :return: HTTP response.

        """
        request = requests.get_mock_post_request(
            user=self.user, is_authenticated=True, data=data)
        return view(request, project_name=self.project.name,
                        task_id=self.task.id)

    # Task view

    def test_task_view_get(self):
        """ Test simple GET of task view. """
        response = self._get_test_view(views.TaskView.as_view())
        self.assertTrue(response.status_code, 200)

    def _test_task_view_action(self, action):
        """ Generate test for task action. """
        response = self._post_test_view(
            views.TaskView.as_view(), {action: 1})
        self.assertEqual(response.status_code, 302)

    def test_task_view_post_accept(self):
        """ Test accept task. """
        self._test_task_view_action('accept')

    def test_task_view_post_reject(self):
        """ Test reject task. """
        self._test_task_view_action('reject')

    def test_task_view_post_close(self):
        """ Test close task. """
        self._test_task_view_action('close')

    def test_task_view_post_reopen(self):
        """ Test reopen task. """
        self._test_task_view_action('reopen')


    # Task edit view

    def test_task_edit_view_get(self):
        response = self._get_test_view(views.TaskEditView.as_view())
        self.assertEqual(response.status_code, 200)

    def test_task_edit_view_post_edit(self):
        response = self._post_test_view(views.TaskEditView.as_view(), {
            'title': 'A title for the task.',
            'description': 'The stuff you write'
        })
        self.assertEqual(response.status_code, 302)

    def test_task_edit_view_post_blank_title(self):
        """ Test edit with blank title. """
        response = self._post_test_view(views.TaskEditView.as_view(), {
            'title': '  '
        })
        self.assertEqual(response.status_code, 200)
