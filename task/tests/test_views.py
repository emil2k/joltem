""" View related tests for task app. """

from joltem.libs.mock import models, requests
from project.tests.test_views import BaseProjectViewTest
from task import views


class BaseTaskViewTest(BaseProjectViewTest):

    """ Test case for view that requires a task. """

    def setUp(self):
        super(BaseTaskViewTest, self).setUp()
        self.task = models.get_mock_task(self.project, self.user)

    def _get(self, view):
        """ Get GET response on given task view.

        :param view: view to test.
        :return: HTTP response.

        """
        request = requests.get_mock_get_request(
            user=self.user, is_authenticated=True)
        return view(request, project_name=self.project.name,
                    task_id=self.task.id)

    def _post(self, view, data):
        """ Get POST response on given task view.

        :param view: view to test.
        :return: HTTP response.

        """
        request = requests.get_mock_post_request(
            user=self.user, is_authenticated=True, data=data)
        return view(request, project_name=self.project.name,
                    task_id=self.task.id)


class TaskViewTest(BaseTaskViewTest):

    """ Test TaskView responses. """

    def test_task_view_get(self):
        """ Test simple GET of task view. """
        response = self._get(views.TaskView.as_view())
        self.assertTrue(response.status_code, 200)

    def _test_task_view_action(self, action):
        """ Generate test for task action. """
        response = self._post(
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


class TaskEditViewTest(BaseTaskViewTest):

    def test_task_edit_view_get(self):
        """ Test simple GET of edit view. """
        response = self._get(views.TaskEditView.as_view())
        self.assertEqual(response.status_code, 200)

    def test_task_edit_view_post_edit(self):
        """ Test edit. """
        response = self._post(views.TaskEditView.as_view(), {
            'title': 'A title for the task.',
            'description': 'The stuff you write'
        })
        self.assertEqual(response.status_code, 302)

    def test_task_edit_view_post_blank_title(self):
        """ Test edit with blank title. Should fail and stay on page. """
        response = self._post(views.TaskEditView.as_view(), {
            'title': '  '
        })
        self.assertEqual(response.status_code, 200)


class TaskCreateViewTest(BaseProjectViewTest):

    def test_task_create_view_get(self):
        """ Test simple GET of create task view. """
        response = self._get(views.TaskCreateView.as_view())
        self.assertEqual(response.status_code, 200)

    def test_task_create_view_post_create(self):
        """ Test create. """
        response = self._post(views.TaskCreateView.as_view(), {
            'title': 'A title for the task.',
            'description': 'The stuff you write',
            'priority': 0,
        })
        self.assertEqual(response.status_code, 302)

    def test_task_create_view_post_blank_title(self):
        """ Test create with blank title. Should fail and stay on page. """
        response = self._post(views.TaskCreateView.as_view(), {
            'title': '  '
        })
        self.assertEqual(response.status_code, 200)


class TaskListViewTests(BaseProjectViewTest):

    def _test_get_task_list(self, view):
        """ Test generator for GET on a task list

        :param view: list view to test.

        """
        response = self._get(view)
        self.assertEqual(response.status_code, 200)

    def test_get_my_open_tasks(self):
        """ Test simple GET of my open tasks view. """
        self._test_get_task_list(views.MyOpenTasksView.as_view())

    def test_get_my_closed_tasks(self):
        """ Test simple GET of my closed tasks view. """
        self._test_get_task_list(views.MyClosedTasksView.as_view())

    def test_get_my_review_tasks(self):
        """ Test simple GET of my tasks to review view. """
        self._test_get_task_list(views.MyReviewTasksView.as_view())

    def test_get_my_reviewed_tasks(self):
        """ Test simple GET of my reviewed tasks view. """
        self._test_get_task_list(views.MyReviewedTasksView.as_view())

    def test_get_all_open_tasks(self):
        """ Test simple GET of all open tasks view. """
        self._test_get_task_list(views.AllOpenTasksView.as_view())

    def test_get_all_closed_tasks(self):
        """ Test simple GET of all closed tasks view. """
        self._test_get_task_list(views.AllClosedTasksView.as_view())
