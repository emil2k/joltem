""" View related tests for solution app. """
from django.core.urlresolvers import reverse
from django.test import TestCase
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


class SolutionReviewViewTest(TestCase):

    """ Test SolutionReviewView responses. """

    def setUp(self):
        self.user = mixer.blend('joltem.user', password='test')
        self.client.login(username=self.user.username, password='test')
        self.solution = mixer.blend('solution.solution', title="Make bread",
                                    description="Mix dough and bake.",
                                    owner__first_name="Jill")
        self.solution.mark_complete()
        self.path = reverse('project:solution:review', args=[
            self.solution.project.name,
            self.solution.id
        ])

    def test_solution_review_view_get(self):
        """ Test simple GET of solution review view. """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)

    def test_solution_vote_no_comment(self):
        """ Test a review vote with no comment.

        A message should be visible to the voter that a comment is required
        for the vote to count.

        """
        mixer.blend('joltem.vote', voter=self.user, voteable=self.solution,
                    voter_impact=1, magnitude=1, is_accepted=True)
        response = self.client.get(self.path)
        self.assertContains(response, "Votes require an explanation")

    def test_solution_vote_with_comment(self):
        """ Test a review vote with a comment posted.

        The message that a comment is required should not be visible now.

        """
        mixer.blend('joltem.vote', voter=self.user, voteable=self.solution,
                    voter_impact=1, magnitude=1, is_accepted=True)
        mixer.blend('joltem.comment', project=self.solution.project,
                    owner=self.user, commentable=self.solution)
        response = self.client.get(self.path)
        print response.content
        self.assertNotContains(response, "Votes require an explanation")


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


MY_REVIEWED_SOLUTIONS_URL = '/{project_name}/solution/reviewed/my/'


class MyReviewedSolutionsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = MY_REVIEWED_SOLUTIONS_URL.format(
            project_name=self.project.name,
        )

    def test_user_has_two_reviewed_solutions(self):
        mixer.blend('solution.solution')

        solutions = mixer.cycle(2).blend(
            'solution.solution', project=self.project)
        for solution in solutions:
            solution.add_vote(voter=self.user, vote_magnitude=1)

        response = self.app.get(self.url, user=self.user, status=200)

        for solution in solutions:
            self.assertContains(response, solution.title)


MY_REVIEW_SOLUTIONS_URL = '/{project_name}/solution/review/my/'


class MyReviewSolutionsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = MY_REVIEW_SOLUTIONS_URL.format(
            project_name=self.project.name,
        )

    def test_user_has_two_solutions_to_review(self):
        mixer.blend(
            'solution.solution',
            project=self.project,
            is_completed=True,
            is_closed=True,
        )

        solutions = mixer.cycle(2).blend(
            'solution.solution',
            project=self.project,
            is_completed=True,
            is_closed=False,
        )

        response = self.app.get(self.url, user=self.user, status=200)

        for solution in solutions:
            self.assertContains(response, solution.title)


MY_INCOMPLETE_SOLUTIONS_URL = '/{project_name}/solution/incomplete/my/'


class MyIncompleteSolutionsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = MY_INCOMPLETE_SOLUTIONS_URL.format(
            project_name=self.project.name,
        )

    def test_user_has_one_incompleted_solution(self):
        mixer.blend(
            'solution.solution',
            is_completed=False,
            is_closed=False,
            owner=self.user,
            project=self.project,
            title='my incomplete solution',
        )

        response = self.app.get(self.url, user=self.user, status=200)

        self.assertContains(response, 'my incomplete solution')


MY_COMPLETE_SOLUTIONS_URL = '/{project_name}/solution/complete/my/'


class MyCompleteSolutionsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = MY_COMPLETE_SOLUTIONS_URL.format(
            project_name=self.project.name,
        )

    def test_user_has_one_completed_solution(self):
        mixer.blend(
            'solution.solution',
            is_completed=True,
            is_closed=False,
            owner=self.user,
            project=self.project,
            title='my completed solution',
        )

        response = self.app.get(self.url, user=self.user, status=200)

        self.assertContains(response, 'my completed solution')


ALL_INCOMPLETE_SOLUTIONS_URL = '/{project_name}/solution/incomplete/'


class IncompleteSolutionsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = ALL_INCOMPLETE_SOLUTIONS_URL.format(
            project_name=self.project.name,
        )

    def test_user_has_one_incompleted_solution(self):
        mixer.blend(
            'solution.solution',
            is_completed=False,
            is_closed=False,
            project=self.project,
            title='incomplete solution',
        )

        response = self.app.get(self.url, user=self.user, status=200)

        self.assertContains(response, 'incomplete solution')


ALL_COMPLETE_SOLUTIONS_URL = '/{project_name}/solution/complete/'


class CompleteSolutionsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = ALL_COMPLETE_SOLUTIONS_URL.format(
            project_name=self.project.name,
        )

    def test_user_has_one_completed_solution(self):
        mixer.blend(
            'solution.solution',
            is_completed=True,
            is_closed=False,
            project=self.project,
            title='completed solution',
        )

        response = self.app.get(self.url, user=self.user, status=200)

        self.assertContains(response, 'completed solution')
