# coding: utf-8
""" View related tests for task app. """
from django_webtest import WebTest
from django.core.urlresolvers import reverse
from joltem.libs import mixer
from joltem.libs.mock import models, requests
from joltem.libs.tests import ViewTestMixin
from project.tests.test_views import BaseProjectViewTest, BaseProjectPermissionsTestCase
from task import views
from task.models import Task


class BaseTaskPermissionsTestCase(BaseProjectPermissionsTestCase):

    """ Base test case for a task's permissions. """


    def setUp(self):
        super(BaseTaskPermissionsTestCase, self).setUp()
        self.task = mixer.blend('task.task', project=self.project,
                                is_closed=False, is_accepted=True,
                                is_reviewed=True)


    def assertStatusCode(self, url_name):
        """ Assert the status code that should be received.

        :param url_name: url name string to reverse.

        """
        kwargs = dict(project_id=self.project.pk, task_id=self.task.pk)
        response = self.client.get(reverse(url_name, kwargs=kwargs))
        self.assertEqual(response.status_code, self.expected_status_code)


class TestTaskPermissions(BaseTaskPermissionsTestCase):

    """ Test permissions to an accepted, open task. """

    expected_status_code = 200
    login_user = True
    is_private = False

    def test_task(self):
        self.assertStatusCode('project:task:task')


class TestTaskPermissionsAnonymous(TestTaskPermissions):

    login_user = False


class TestPrivateTaskPermissions(TestTaskPermissions):

    expected_status_code = 404
    is_private = True


class TestPrivateTaskPermissionsAnonymous(TestPrivateTaskPermissions):

    login_user = False


class TestPrivateTasksPermissionsInvitee(TestTaskPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "invitee"


class TestPrivateTasksPermissionsAdmin(TestTaskPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "admin"


class TestPrivateTasksPermissionsManager(TestTaskPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "manager"


class TestPrivateTasksPermissionsDeveloper(TestTaskPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "developer"


class TestTasksListsPermissions(BaseProjectPermissionsTestCase):

    """ Test permissions to tasks lists. """

    expected_status_code = 200
    login_user = True
    is_private = False

    def test_my_open_tasks(self):
        self.assertStatusCode('project:task:my_open')

    def test_my_closed_tasks(self):
        self.assertStatusCode('project:task:my_closed')

    def test_my_review_tasks(self):
        self.assertStatusCode('project:task:my_review')

    def test_my_reviewed_tasks(self):
        self.assertStatusCode('project:task:my_reviewed')

    def test_all_open_tasks(self):
        self.assertStatusCode('project:task:all_open')

    def test_all_closed_tasks(self):
        self.assertStatusCode('project:task:all_closed')


class TestTaskListsPermissionsAnonymous(TestTasksListsPermissions):

    login_user = False


class TestPrivateTaskListsPermissions(TestTasksListsPermissions):

    expected_status_code = 404
    is_private = True


class TestPrivateTaskListsPermissionsAnonymous(TestPrivateTaskListsPermissions):

    login_user = False


class TestPrivateTaskListsPermissionsInvitee(TestTasksListsPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "invitee"


class TestPrivateTaskListsPermissionsAdmin(
    TestPrivateTaskListsPermissionsInvitee):

    group_name = "admin"


class TestPrivateTaskListsPermissionsManager(
    TestPrivateTaskListsPermissionsInvitee):

    group_name = "manager"


class TestPrivateTaskListsPermissionsDeveloper(
    TestPrivateTaskListsPermissionsInvitee):

    group_name = "developer"


class BaseTaskViewTest(BaseProjectViewTest):

    """ Test case for view that requires a task. """

    def setUp(self):
        super(BaseTaskViewTest, self).setUp()
        self.task = models.get_mock_task(self.project, self.user)

    def _get(self, view, task=None):
        """ Get GET response on given task view.

        :param view: view to test.
        :return: HTTP response.

        """
        if task is None:
            task = self.task
        request = requests.get_mock_get_request(
            user=self.user, is_authenticated=True)
        return view(request, project_id=task.project.id,
                    task_id=task.id)

    def _post(self, view, data):
        """ Get POST response on given task view.

        :param view: view to test.
        :return: HTTP response.

        """
        request = requests.get_mock_post_request(
            user=self.user, is_authenticated=True, data=data)
        return view(request, project_id=self.project.id,
                    task_id=self.task.id)


class TaskViewTest(BaseTaskViewTest):

    """ Test TaskView responses. """

    def test_task_view_get(self):
        """ Test simple GET of task view. """
        task = mixer.blend('task.task', project=self.project)
        response = self._get(views.TaskView.as_view(), task=task)
        response = response.render()
        self.assertContains(response, '<h4><a href="/user/%s/">%s</a></h4>' % (
            task.owner.username, task.owner.first_name))
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
        url = reverse('project:task:task', kwargs=dict(
                      project_id=self.task.project_id, task_id=self.task.pk))

        # Close by owner
        self.client.login(
            username=self.task.owner.username, password='bill_password')
        self.client.post(url, data=dict(close=1))
        task = Task.objects.get()
        self.assertTrue(task.is_closed)
        Task.objects.filter(pk=task.pk).update(is_closed=False)

        # Close by any user
        user = mixer.blend('joltem.user', password='user')
        self.client.login(username=user.username, password='user')
        self.client.post(url, data=dict(close=1))
        task = Task.objects.get()
        self.assertFalse(task.is_closed)

        # Close by manager
        self.project.manager_set.add(user)
        self.client.post(url, data=dict(close=1))
        task = Task.objects.get()
        self.assertTrue(task.is_closed)
        self.project.manager_set.remove(user)
        Task.objects.filter(pk=task.pk).update(is_closed=False)

        # Close by admin
        self.project.admin_set.add(user)
        self.client.post(url, data=dict(close=1))
        task = Task.objects.get()
        self.assertTrue(task.is_closed)

    def test_task_view_post_reopen(self):
        """ Test reopen task. """
        url = reverse('project:task:task', kwargs=dict(
                      project_id=self.task.project_id, task_id=self.task.pk))

        task = Task.objects.get()
        Task.objects.filter(pk=task.pk).update(is_closed=True)

        # Reopen by owner
        self.client.login(
            username=self.task.owner.username, password='bill_password')
        self.client.post(url, data=dict(reopen=1))
        task = Task.objects.get()
        self.assertFalse(task.is_closed)
        Task.objects.filter(pk=task.pk).update(is_closed=True)

        # Reopen by any user
        user = mixer.blend('joltem.user', password='user')
        self.client.login(username=user.username, password='user')
        self.client.post(url, data=dict(reopen=1))
        task = Task.objects.get()
        self.assertTrue(task.is_closed)

        # Reopen by manager
        self.project.manager_set.add(user)
        self.client.post(url, data=dict(reopen=1))
        task = Task.objects.get()
        self.assertFalse(task.is_closed)
        self.project.manager_set.remove(user)
        Task.objects.filter(pk=task.pk).update(is_closed=True)

        # Reopen by admin
        self.project.admin_set.add(user)
        self.client.post(url, data=dict(reopen=1))
        task = Task.objects.get()
        self.assertFalse(task.is_closed)


class TaskListViewTests(BaseProjectViewTest):

    def _test_get_task_list(self, view):
        """ Test generator for GET on a task list

        :param view: list view to test.

        """
        response = self._get(view)
        self.assertEqual(response.status_code, 200)

    def test_get_my_open_tasks(self):
        """ Test simple GET of my open tasks view. """
        task = mixer.blend(
            'task.task', project=self.project, owner=self.user,
            is_accepted=True)
        response = self._get(views.MyOpenTasksView.as_view())
        response = response.render()
        self.assertContains(
            response,
            'by <a href="/user/%s/" class="muted">%s</a>' % (
                task.owner.username, task.owner.first_name
            ))

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


TASK_URL = '/{project_id}/task/{task_id}/'

TASK_CREATE_URL = '/{project_id}/task/new/'
TASK_CREATE_FORM_ID = 'task-create-form'


class TaskCreateTest(WebTest, ViewTestMixin):

    csrf_checks = False

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = TASK_CREATE_URL.format(project_id=self.project.id)

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

        expected_url = TASK_URL.format(
            project_id=self.project.id, task_id=task.pk)
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

        self.url = TASK_CREATE_URL.format(project_id=self.project.id)

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


TASK_EDIT_URL = '/{project_id}/task/{task_id}/edit/'
TASK_EDIT_FORM_ID = 'task-edit-form'


class TaskEditTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')
        self.task = mixer.blend('task.task', project=self.project,
                                owner=self.user)

        self.url = TASK_EDIT_URL.format(
            project_id=self.project.id,
            task_id=self.task.pk
        )

    def test_redirect_to_login_page_when_user_is_not_logged_in(self):
        response = self.app.get(self.url)

        self._test_sign_in_redirect_url(response, self.url)

    def test_404_when_non_owner_gets_task_edit_page(self):
        not_owner = mixer.blend('joltem.user')

        self.app.get(self.url, user=not_owner, status=404)

    def test_task_is_successfully_updated(self):

        # Edit by owner
        response = self.app.get(self.url, user=self.user)

        form = response.forms[TASK_EDIT_FORM_ID]
        form['title'] = 'new title'
        response = form.submit()

        expected_url = TASK_URL.format(
            project_id=self.project.id, task_id=self.task.pk)
        self.assertRedirects(response, expected_url)

        task = Task.objects.get()
        self.assertEqual(task.title, 'new title')

        (admin, manager) = mixer.cycle(2).blend('joltem.user')
        self.project.admin_set.add(admin)
        self.project.manager_set.add(manager)

        # Edit by admin
        response = self.app.get(self.url, user=admin)

        form = response.forms[TASK_EDIT_FORM_ID]
        form['title'] = 'admin title'
        form.submit()

        task = Task.objects.get()
        self.assertEqual(task.title, 'admin title')

        # Edit by manager
        response = self.app.get(self.url, user=manager)

        form = response.forms[TASK_EDIT_FORM_ID]
        form['title'] = 'manager title'
        form.submit()

        task = Task.objects.get()
        self.assertEqual(task.title, 'manager title')

    def test_title_must_contain_printable_characters(self):
        response = self.app.get(self.url, user=self.user)

        form = response.forms[TASK_EDIT_FORM_ID]
        form['title'] = ' \n\t'
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'title',
            errors='This field cannot be blank.',
        )


class TaskEditRequiredFieldsTest(WebTest):

    error_message = 'This field is required.'

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')
        self.task = mixer.blend(
            'task.task',
            project=self.project,
            owner=self.user,
            priority=1,
        )

        self.url = TASK_EDIT_URL.format(
            project_id=self.project.id,
            task_id=self.task.pk
        )

    def test_title_is_required(self):
        response = self.app.get(self.url, user=self.user)

        form = response.forms[TASK_EDIT_FORM_ID]
        form['title'] = ''
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'title',
            errors=self.error_message,
        )

    def test_description_is_not_required(self):
        response = self.app.get(self.url, user=self.user)

        form = response.forms[TASK_EDIT_FORM_ID]
        form['title'] = ''
        form['description'] = ''
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'title',
            errors=self.error_message,
        )

    def test_priority_is_required(self):
        response = self.app.get(self.url, user=self.user)

        form = response.forms[TASK_EDIT_FORM_ID]
        form['priority'].options[1] = (u'1', False)
        response = form.submit()

        self.assertFormError(
            response,
            'form',
            'priority',
            errors=self.error_message,
        )
