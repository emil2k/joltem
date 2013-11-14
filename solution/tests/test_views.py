""" View related tests for solution app. """

from joltem.libs.mock import models, requests
from project.tests.test_views import BaseProjectViewTest
from solution import views
from solution.models import Solution


class BaseSolutionViewTest(BaseProjectViewTest):

    """ Test case for view that requires a solution. """

    def setUp(self):
        super(BaseSolutionViewTest, self).setUp()
        self.solution = models.get_mock_solution(self.project, self.user)


    def _get(self, view):
        """ Get GET response on given solution view.

        :param view: view to test.
        :return: HTTP response.

        """
        request = requests.get_mock_get_request(
            user=self.user, is_authenticated=True)
        return view(request, project_name=self.project.name,
                        solution_id=self.solution.id)

    def _post(self, view, data):
        """ Get POST response on given solution view.

        :param view: view to test.
        :return: HTTP response.

        """
        request = requests.get_mock_post_request(
            user=self.user, is_authenticated=True, data=data)
        return view(request, project_name=self.project.name,
                        solution_id=self.solution.id)

class SolutionViewTest(BaseSolutionViewTest):

    """ Test SolutionView responses. """

    def test_solution_view_get(self):
        """ Test simple GET of solution view. """
        response = self._get(views.SolutionView.as_view())
        self.assertTrue(response.status_code, 200)

    def _test_solution_view_action(self, action):
        """ Generate test for solution action. """
        response = self._post(
            views.SolutionView.as_view(), {action: 1})
        self.assertEqual(response.status_code, 302)

    def test_solution_view_post_complete(self):
        """ Test mark solution complete. """
        self._test_solution_view_action('complete')

    def test_solution_view_post_incomplete(self):
        """ Test mark solution incomplete. """
        self._test_solution_view_action('incomplete')

    def test_solution_view_post_close(self):
        """ Test close solution. """
        self._test_solution_view_action('close')

    def test_solution_view_post_reopen(self):
        """ Test reopen solution. """
        self._test_solution_view_action('reopen')


class SolutionEditView(BaseSolutionViewTest):

    """ Test SolutionEditView responses. """

    def test_solution_edit_view_get(self):
        """ Test simple GET of solution edit view. """
        response = self._get(views.SolutionEditView.as_view())
        self.assertTrue(response.status_code, 200)

    def test_solution_edit_post(self):
        """ Test edit. """
        response = self._post(views.SolutionEditView.as_view(), {
            'title': 'new title',
            'description': 'new description'
        })
        self.assertTrue(response.status_code, 302)
        reloaded = models.load_model(Solution, self.solution)
        self.assertEqual(reloaded.title, 'new title')
        self.assertEqual(reloaded.description, 'new description')

