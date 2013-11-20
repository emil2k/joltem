# coding: utf-8
""" View related tests for task app. """
from django_webtest import WebTest

from joltem.libs.mock import models, requests
from joltem.libs.mix import mixer
from joltem.libs.tests import ViewTestMixin
from project.tests.test_views import BaseProjectViewTest

from task import views
from task.models import Task


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


TASK_CREATE_URL = '/{project_name}/task/new/'
TASK_EDIT_URL = '/{project_name}/task/{task_id}/'
TASK_CREATE_FORM_ID = 'task-create-form'


class TaskCreateTest(WebTest, ViewTestMixin):

    csrf_checks = False

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = TASK_CREATE_URL.format(project_name=self.project.name)

    def test_redirect_to_login_page_when_user_is_not_logged_in(self):
        response = self.app.get(self.url)

        self._test_sign_in_redirect_url(response, self.url)

    def test_task_is_successfully_created(self):
        response = self.app.get(self.url, user=self.user)

        form = response.forms[TASK_CREATE_FORM_ID]
        form['title'] = 'dummy title'
        form['description'] = 'dummy description'
        form['priority'] = 0
        response = form.submit()

        task = Task.objects.get()

        expected_url = TASK_EDIT_URL.format(project_name=self.project.name,
                                            task_id=task.pk)
        self.assertRedirects(response, expected_url)

    def test_title_must_contain_printable_characters(self):
        response = self.app.get(self.url, user=self.user)

        form = response.forms[TASK_CREATE_FORM_ID]
        form['title'] = ' \n\t'
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'title',
            errors='This field cannot be blank.',
        )

    def test_project_id_substitution_is_ignored(self):
        project_substitute = mixer.blend('project.project')

        post_params = {
            'title': 'dummy',
            'priority': 0,
            'project': project_substitute.pk,
        }
        self.app.post(self.url, post_params, user=self.user)

        task = Task.objects.get()

        self.assertEqual(task.project_id, self.project.pk)

    def test_owner_id_substitution_is_ignored(self):
        owner_substitute = mixer.blend('joltem.user')

        post_params = {
            'title': 'dummy',
            'priority': 0,
            'owner': owner_substitute.pk,
        }
        self.app.post(self.url, post_params, user=self.user)

        task = Task.objects.get()

        self.assertEqual(task.owner_id, self.user.pk)


class TaskCreateRequiredFieldsTest(WebTest):

    error_message = 'This field is required.'

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = TASK_CREATE_URL.format(project_name=self.project.name)

    def test_title_is_required(self):
        response = self.app.get(self.url, user=self.user)

        form = response.forms[TASK_CREATE_FORM_ID]
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'title',
            errors=self.error_message,
        )

    def test_description_is_not_required(self):
        response = self.app.get(self.url, user=self.user)

        form = response.forms[TASK_CREATE_FORM_ID]
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'description',
            errors=[],
        )

    def test_priority_is_required(self):
        response = self.app.get(self.url, user=self.user)

        form = response.forms[TASK_CREATE_FORM_ID]
        form['priority'].options[1] = (u'1', False)
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'priority',
            errors=self.error_message,
        )
