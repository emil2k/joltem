""" View related tests for solution app. """
from django_webtest import WebTest

from joltem.libs import mixer
from joltem.libs.mock import models, requests
from joltem.libs.tests import ViewTestMixin
from project.tests.test_views import BaseProjectViewTest
from solution import views


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
        return view(
            request, project_name=self.project.name,
            solution_id=self.solution.id)

    def _post(self, view, data, **headers):
        """ Get POST response on given solution view.

        :param view: view to test.
        :return: HTTP response.

        """
        request = requests.get_mock_post_request(
            user=self.user, is_authenticated=True, data=data, **headers)
        return view(
            request, project_name=self.project.name,
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
        self.solution = self.solution.__class__.objects.get(
            pk=self.solution.pk)

    def test_solution_view_post_complete(self):
        """ Test mark solution complete. """
        self.solution.mark_open()
        self.solution.mark_incomplete()
        self._test_solution_view_action('complete')
        self.assertTrue(self.solution.is_completed)

    def test_solution_view_post_incomplete(self):
        """ Test mark solution incomplete. """
        self.solution.mark_complete()
        self._test_solution_view_action('incomplete')
        self.assertFalse(self.solution.is_completed)

    def test_solution_view_post_close(self):
        """ Test close solution. """
        self.solution.mark_open()
        self._test_solution_view_action('close')
        self.assertTrue(self.solution.is_closed)

    def test_solution_view_post_reopen(self):
        """ Test reopen solution. """
        self.solution.mark_close()
        self._test_solution_view_action('reopen')
        self.assertFalse(self.solution.is_closed)

    def test_solution_empty_post(self):
        response = self._post(
            views.SolutionView.as_view(), {})
        self.assertEqual(response.status_code, 302)

    def test_solution_comment_post(self):
        self._post(views.SolutionView.as_view(), {'comment': 'comment'})
        comments = self.solution.comment_set.all()
        self.assertTrue(comments.count())
        comment = comments[0]
        self.assertEqual(comment.owner, self.solution.owner)

    def test_solution_comment_edit_delete(self):
        comment = mixer.blend('joltem.comment',
                              comment='comment',
                              commentable=self.solution,
                              owner=self.solution.owner)

        self._post(views.SolutionView.as_view(), {
            'comment_id': comment.pk, 'comment_edit': 'new comment'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        comment = self.solution.comment_set.get()
        self.assertEqual(comment.comment, 'new comment')

        self._post(views.SolutionView.as_view(), {
            'comment_id': comment.pk, 'comment_delete': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertFalse(self.solution.comment_set.count())


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
        reloaded = models.load_model(self.solution)
        self.assertEqual(reloaded.title, 'new title')
        self.assertEqual(reloaded.description, 'new description')


class SolutionReviewView(BaseSolutionViewTest):

    """ Test SolutionReviewView responses. """

    def test_solution_review_view_get(self):
        """ Test simple GET of solution review view. """
        response = self._get(views.SolutionReviewView.as_view())
        self.assertTrue(response.status_code, 200)


class SolutionCreateView(BaseSolutionViewTest):

    """ Test SolutionCreateView responses. """

    def test_solution_create_view_get(self):
        """ Test simple GET of solution commits view. """
        response = self._get(views.SolutionCreateView.as_view())
        self.assertTrue(response.status_code, 200)

    def test_solution_create(self):
        """ Test creating solution with no title and description.

        When viewed defaults to tasks title.

        """
        response = self._post(views.SolutionCreateView.as_view(), {})
        self.assertTrue(response.status_code, 302)


class SolutionListViewTests(BaseProjectViewTest):

    def _test_get_solution_list(self, view):
        """ Test generator for GET on a solution list

        :param view: list view to test.

        """
        response = self._get(view)
        self.assertEqual(response.status_code, 200)

    def test_get_my_incomplete_solutions(self):
        """ Test simple GET of my incomplete solutions view. """
        self._test_get_solution_list(views.MyIncompleteSolutionsView.as_view())

    def test_get_my_complete_solutions(self):
        """ Test simple GET of my complete solutions view. """
        self._test_get_solution_list(views.MyCompleteSolutionsView.as_view())

    def test_get_my_review_solutions(self):
        """ Test simple GET of my solutions to review view. """
        for i in range(0, 3):  # to test generators
            models.get_mock_solution(
                self.project, models.get_mock_user('dan' + str(i)),
                is_completed=True)
        self._test_get_solution_list(views.MyReviewSolutionsView.as_view())

    def test_get_my_reviewed_solutions(self):
        """ Test simple GET of my reviewed solutions view. """
        for i in range(0, 3):  # to test generators
            s = models.get_mock_solution(
                self.project, models.get_mock_user('dan' + str(i)),
                is_completed=True)
            s.put_vote(self.user, 3)
        self._test_get_solution_list(views.MyReviewedSolutionsView.as_view())

    def test_get_all_incomplete_solutions(self):
        """ Test simple GET of all incomplete solutions view. """
        self._test_get_solution_list(
            views.AllIncompleteSolutionsView.as_view())

    def test_get_all_complete_solutions(self):
        """ Test simple GET of all complete solutions view. """
        self._test_get_solution_list(views.AllCompleteSolutionsView.as_view())


SOLUTION_COMMITS_URL = '/{project_name}/solution/{solution_id}/commits/'
SOLUTION_COMMITS_REPO_URL = '/{project_name}/solution/{solution_id}/commits/repository/{repo_id}/'


class SolutionCommitsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.solution = mixer.blend(
            'solution.solution',
        )

        self.url = SOLUTION_COMMITS_URL.format(
            project_name=self.solution.project.name,
            solution_id=self.solution.pk,
        )

    def test_redirect_to_login_page_when_user_is_not_logged_in(self):
        response = self.app.get(self.url)

        self._test_sign_in_redirect_url(response, self.url)

    def test_it_is_ok_if_project_has_no_repositories(self):
        response = self.app.get(self.url, user=self.user)

        self.assertContains(response, 'The project has no repositories')

    def test_404_if_project_does_not_exist(self):
        url_with_faked_project = SOLUTION_COMMITS_URL.format(
            project_name='blah',
            solution_id=self.solution.pk,
        )

        self.app.get(url_with_faked_project, user=self.user, status=404)

    def test_404_if_solution_does_not_exist(self):
        url_with_faked_solution = SOLUTION_COMMITS_URL.format(
            project_name=self.solution.project.name,
            solution_id=0,
        )

        self.app.get(url_with_faked_solution, user=self.user, status=404)

    def test_404_if_repository_does_not_exist(self):
        url_with_faked_repo = SOLUTION_COMMITS_REPO_URL.format(
            project_name=self.solution.project.name,
            solution_id=self.solution.pk,
            repo_id='0'
        )

        self.app.get(url_with_faked_repo, user=self.user, status=404)
