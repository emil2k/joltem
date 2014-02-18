""" View related tests for solution app. """
from django.core.urlresolvers import reverse
from django.test import TestCase
from django_webtest import WebTest

from joltem.libs import mixer
from joltem.libs.mock import models, requests
from joltem.libs.tests import ViewTestMixin
from project.tests.test_views import BaseProjectViewTest, BaseProjectPermissionsTestCase
from solution import views
from solution.models import Solution


class BaseSolutionPermissionsTestCase(BaseProjectPermissionsTestCase):

    """ Base test case for a solution's permissions.

    :param is_complete: whether solution is complete.

    """

    is_complete = None

    def setUp(self):
        super(BaseSolutionPermissionsTestCase, self).setUp()
        self.solution = mixer.blend('solution.solution', project=self.project)
        if self.is_complete:
            self.solution.mark_complete(impact=1)

    def assertStatusCode(self, url_name):
        """ Assert the status code that should be received.

        :param url_name: url name string to reverse.

        """
        kwargs = dict(project_id=self.project.pk, solution_id=self.solution.pk)
        response = self.client.get(reverse(url_name, kwargs=kwargs))
        self.assertEqual(response.status_code, self.expected_status_code)


class TestSolutionPermissions(BaseSolutionPermissionsTestCase):

    """ Test permissions to complete solution. """

    expected_status_code = 200
    login_user = True
    is_private = False
    is_complete = True

    def test_solution(self):
        """ Test solution view. """
        self.assertStatusCode('project:solution:solution')

    def test_solution_commits(self):
        """ Test solution commits view. """
        self.assertStatusCode('project:solution:commits')

    def test_solution_review(self):
        """ Test solution review view. """
        self.assertStatusCode('project:solution:review')


class TestSolutionPermissionsAnonymous(TestSolutionPermissions):

    expected_status_code = 200
    login_user = False
    is_private = False


class TestPrivateSolutionPermissions(TestSolutionPermissions):

    expected_status_code = 404
    login_user = True
    is_private = True


class TestPrivateSolutionPermissionsAnonymous(TestSolutionPermissions):

    expected_status_code = 404
    login_user = False
    is_private = True


class TestPrivateSolutionPermissionsInvitee(TestSolutionPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "invitee"


class TestPrivateSolutionPermissionsAdmin(TestSolutionPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "admin"


class TestPrivateSolutionPermissionsManager(TestSolutionPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "manager"


class TestPrivateSolutionPermissionsDeveloper(TestSolutionPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "developer"


class TestSolutionListsPermissions(BaseProjectPermissionsTestCase):

    """ Test permissions to solutions lists. """

    expected_status_code = 200
    login_user = True
    is_private = False

    def test_my_complete_solutions(self):
        """ Test permissions to my complete solution list. """
        self.assertStatusCode('project:solution:my_complete')

    def test_my_incomplete_solutions(self):
        """ Test permissions to my incomplete solution list. """
        self.assertStatusCode('project:solution:my_incomplete')

    def test_my_review_solutions(self):
        """ Test permissions to my review solution list. """
        self.assertStatusCode('project:solution:my_review')

    def test_my_reviewed_solutions(self):
        """ Test permissions to my reviewed solution list. """
        self.assertStatusCode('project:solution:my_reviewed')

    def test_all_complete_solutions(self):
        """ Test permissions to all complete solution list. """
        self.assertStatusCode('project:solution:all_complete')

    def test_all_incomplete_solutions(self):
        """ Test permissions to all incomplete solution list. """
        self.assertStatusCode('project:solution:all_incomplete')


class TestSolutionListsPermissionsAnonymous(TestSolutionListsPermissions):

    expected_status_code = 200
    login_user = False
    is_private = False


class TestPrivateSolutionsListPermissions(TestSolutionListsPermissions):

    expected_status_code = 404
    login_user = True
    is_private = True


class TestPrivateSolutionsListPermissionsAnonymous(
        TestSolutionListsPermissions):

    expected_status_code = 404
    login_user = False
    is_private = True


class TestPrivateSolutionsListPermissionsInvitee(TestSolutionListsPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "invitee"


class TestPrivateSolutionsListPermissionsAdmin(TestSolutionListsPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "admin"


class TestPrivateSolutionsListPermissionsManager(TestSolutionListsPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "manager"


class TestPrivateSolutionsListPermissionsDeveloper(TestSolutionListsPermissions):

    expected_status_code = 200
    login_user = True
    is_private = True
    group_name = "developer"


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
            request, project_id=self.project.id,
            solution_id=self.solution.id)

    def _post(self, view, data, **headers):
        """ Get POST response on given solution view.

        :param view: view to test.
        :return: HTTP response.

        """
        request = requests.get_mock_post_request(
            user=self.user, is_authenticated=True, data=data, **headers)
        return view(
            request, project_id=self.project.id,
            solution_id=self.solution.id)


class SolutionViewOwnerTest(TestCase):

    """ Test SolutionView responses for owner of the solution. """

    def setUp(self):
        self.user = mixer.blend('joltem.user', password='test')
        self.solution = mixer.blend('solution.solution', owner=self.user)
        self.path = reverse('project:solution:solution', args=[
            self.solution.project.id,
            self.solution.id
        ])
        self.client.login(username=self.user.username, password='test')

    def test_incomplete_get(self):
        """ Test GET of open and incomplete solution by owner.

        Visible : edit, create task, close, and complete dialog
        Invisible : suggest solution, mark incomplete, reopen

        """
        self.assertFalse(self.solution.is_completed)
        self.assertFalse(self.solution.is_closed)
        response = self.client.get(self.path)
        self.assertContains(response, 'edit</a>')
        self.assertContains(response, 'create task</a>')
        self.assertContains(response, 'close</button>')
        self.assertContains(
            response, '<div id="compensation-q" class="alert">')
        self.assertNotContains(response, 'reopen</button>')
        self.assertNotContains(response, 'suggest solution</a>')
        self.assertNotContains(response, 'mark incomplete</button>')

    def test_complete_get(self):
        """ Test GET of open and complete solution by owner.

        Visible : edit and mark incomplete
        Invisible : create task, close, complete dialog, reopen,
            and suggest solution

        """
        self.solution.mark_complete(5)
        self.assertTrue(self.solution.is_completed)
        self.assertFalse(self.solution.is_closed)
        response = self.client.get(self.path)
        self.assertContains(response, 'edit</a>')
        self.assertContains(response, 'mark incomplete</button>')
        self.assertNotContains(response, 'create task</a>')
        self.assertNotContains(response, 'close</button>')
        self.assertNotContains(response, 'reopen</button>')
        self.assertNotContains(response,
                               '<div id="compensation-q" class="alert">')
        self.assertNotContains(response, 'suggest solution</a>')

    def test_closed_get(self):
        """ Test GET of closed solution by owner.

        Visible : reopen
        Invisible : edit, complete dialog, mark incomplete, close, create task,
            and suggest solution

        """
        self.solution.mark_close()
        self.assertTrue(self.solution.is_closed)
        response = self.client.get(self.path)
        self.assertContains(response, 'reopen</button>')
        self.assertNotContains(response, 'edit</a>')
        self.assertNotContains(response, 'mark incomplete</button>')
        self.assertNotContains(response, 'create task</a>')
        self.assertNotContains(response, 'close</button>')
        self.assertNotContains(response,
                               '<div id="compensation-q" class="alert">')
        self.assertNotContains(response, 'suggest solution</a>')


class SolutionViewUserTest(TestCase):

    """ Test SolutionView responses for a signed in user.

    The user is not owner of the solution.

    """

    def setUp(self):
        self.user = mixer.blend('joltem.user', password='test')
        self.solution = mixer.blend('solution.solution')
        self.path = reverse('project:solution:solution', args=[
            self.solution.project.id,
            self.solution.id
        ])
        self.client.login(username=self.user.username, password='test')

    def test_incomplete_get(self):
        """ Test GET of open and incomplete solution by a user.

        Visible : create task and suggest solution
        Invisible : edit, close, complete dialog, mark incomplete, reopen

        """
        self.assertFalse(self.solution.is_completed)
        self.assertFalse(self.solution.is_closed)
        response = self.client.get(self.path)
        self.assertContains(response, 'create task</a>')
        self.assertContains(response, 'suggest solution</a>')
        self.assertNotContains(response, 'edit</a>')
        self.assertNotContains(response, 'close</button>')
        self.assertNotContains(
            response, '<div id="compensation-q" class="alert">')
        self.assertNotContains(response, 'reopen</button>')
        self.assertNotContains(response, 'mark incomplete</button>')

    def test_complete_get(self):
        """ Test GET of open and complete solution by a user.

        Invisible : all

        """
        self.solution.mark_complete(5)
        self.assertTrue(self.solution.is_completed)
        self.assertFalse(self.solution.is_closed)
        response = self.client.get(self.path)
        self.assertNotContains(response, 'edit</a>')
        self.assertNotContains(response, 'mark incomplete</button>')
        self.assertNotContains(response, 'create task</a>')
        self.assertNotContains(response, 'close</button>')
        self.assertNotContains(response, 'reopen</button>')
        self.assertNotContains(response,
                               '<div id="compensation-q" class="alert">')
        self.assertNotContains(response, 'suggest solution</a>')

    def test_closed_get(self):
        """ Test GET of closed solution by a user.

        Invisible : all

        """
        self.solution.mark_close()
        self.assertTrue(self.solution.is_closed)
        response = self.client.get(self.path)
        self.assertNotContains(response, 'edit</a>')
        self.assertNotContains(response, 'mark incomplete</button>')
        self.assertNotContains(response, 'create task</a>')
        self.assertNotContains(response, 'close</button>')
        self.assertNotContains(response, 'reopen</button>')
        self.assertNotContains(response,
                               '<div id="compensation-q" class="alert">')
        self.assertNotContains(response, 'suggest solution</a>')


class SolutionViewAnonymousTest(TestCase):

    """ Test SolutionView responses for an anonymous user.

    The user is not signed in.

    """

    def setUp(self):
        self.solution = mixer.blend('solution.solution')
        self.path = reverse('project:solution:solution', args=[
            self.solution.project.id,
            self.solution.id
        ])

    def test_incomplete_get(self):
        """ Test GET of open and incomplete solution by an anonymous user.

        Invisible : all

        """
        self.assertFalse(self.solution.is_completed)
        self.assertFalse(self.solution.is_closed)
        response = self.client.get(self.path)
        self.assertNotContains(response, 'create task</a>')
        self.assertNotContains(response, 'suggest solution</a>')
        self.assertNotContains(response, 'edit</a>')
        self.assertNotContains(response, 'close</button>')
        self.assertNotContains(
            response, '<div id="compensation-q" class="alert">')
        self.assertNotContains(response, 'reopen</button>')
        self.assertNotContains(response, 'mark incomplete</button>')

    def test_complete_get(self):
        """ Test GET of open and complete solution by an anonymous user.

        Invisible : all

        """
        self.solution.mark_complete(5)
        self.assertTrue(self.solution.is_completed)
        self.assertFalse(self.solution.is_closed)
        response = self.client.get(self.path)
        self.assertNotContains(response, 'edit</a>')
        self.assertNotContains(response, 'mark incomplete</button>')
        self.assertNotContains(response, 'create task</a>')
        self.assertNotContains(response, 'close</button>')
        self.assertNotContains(response, 'reopen</button>')
        self.assertNotContains(response,
                               '<div id="compensation-q" class="alert">')
        self.assertNotContains(response, 'suggest solution</a>')

    def test_closed_get(self):
        """ Test GET of closed solution by an anonymous.

        Invisible : all

        """
        self.solution.mark_close()
        self.assertTrue(self.solution.is_closed)
        response = self.client.get(self.path)
        self.assertNotContains(response, 'edit</a>')
        self.assertNotContains(response, 'mark incomplete</button>')
        self.assertNotContains(response, 'create task</a>')
        self.assertNotContains(response, 'close</button>')
        self.assertNotContains(response, 'reopen</button>')
        self.assertNotContains(response,
                               '<div id="compensation-q" class="alert">')
        self.assertNotContains(response, 'suggest solution</a>')


class SolutionViewTest(BaseSolutionViewTest):

    """ Test SolutionView responses. """

    def test_solution_view_get(self):
        """ Test simple GET of solution view. """
        response = self._get(views.SolutionView.as_view())
        self.assertTrue(response.status_code, 200)

    def _test_solution_view_action(self, action, **data):
        """ Generate test for solution action. """
        data.update({action: 1})
        response = self._post(
            views.SolutionView.as_view(), data)
        self.assertEqual(response.status_code, 302)
        self.solution = self.solution.__class__.objects.get(
            pk=self.solution.pk)

    def test_solution_view_post_complete(self):
        """ Test mark solution complete. """
        self.solution.mark_open()
        self.solution.mark_incomplete()
        self._test_solution_view_action('complete', compensation_value=5)
        self.assertTrue(self.solution.is_completed)
        self.assertEqual(self.solution.impact, 5)

    def test_solution_view_post_incomplete(self):
        """ Test mark solution incomplete. """
        self.solution.mark_complete(5)
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
        self.solution.is_archived = True
        self.solution.save()
        self.assertFalse(self.solution.comment_set.all())
        self._post(views.SolutionView.as_view(), {'comment': 'comment'})
        self.assertFalse(self.solution.comment_set.all())

        self.solution.is_archived = False
        self.solution.save()
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

        reloaded.is_archived = True
        reloaded.save()
        response = self._post(views.SolutionEditView.as_view(), {
            'title': 'another new title',
            'description': 'another new description'
        })
        reloaded = models.load_model(self.solution)
        self.assertEqual(reloaded.title, 'new title')
        self.assertEqual(reloaded.description, 'new description')


class SolutionReviewViewOwnerTest(TestCase):

    """ Test SolutionReviewView responses for owner of solution. """

    def setUp(self):
        self.user = mixer.blend('joltem.user', password='test')
        self.solution = mixer.blend('solution.solution', owner=self.user)
        self.solution.mark_complete(5)
        self.client.login(username=self.user.username, password='test')
        self.path = reverse('project:solution:review', args=[
            self.solution.project.id,
            self.solution.id
        ])

    def test_change_evaluation(self):
        """ Test change evaluation. """
        self.assertEqual(self.solution.impact, 5)
        response = self.client.post(self.path, {'compensation_value': 100,
                                                'change_value': 1})
        self.assertRedirects(response, self.path)
        loaded = Solution.objects.get(id=self.solution.id)
        self.assertEqual(loaded.impact, 100)


class SolutionReviewViewTest(TestCase):

    """ Test SolutionReviewView responses. """

    def setUp(self):
        self.user = mixer.blend('joltem.user', password='test')
        self.client.login(username=self.user.username, password='test')
        self.solution = mixer.blend('solution.solution', title="Make bread",
                                    description="Mix dough and bake.",
                                    owner__first_name="Jill")
        self.solution.mark_complete(5)
        self.path = reverse('project:solution:review', args=[
            self.solution.project.id,
            self.solution.id
        ])

    def test_solution_review_view_get(self):
        """ Test simple GET of solution review view. """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)

    def test_solution_is_archived_review_view_get(self):
        solution = mixer.blend('solution.solution', is_archived=True)
        path = reverse('project:solution:review', args=[
            solution.project_id,
            solution.pk
        ])
        response = self.client.get(path)
        self.assertNotContains(response, '<form method="post">')

    def test_solution_negative_vote_no_comment(self):
        """ Test a negative review vote with no comment.

        The message that a comment is required should be visible now.

        """
        mixer.blend('joltem.vote', voter=self.user, voteable=self.solution,
                    voter_impact=1, is_accepted=False)
        response = self.client.get(self.path)
        self.assertContains(response, "Votes require an explanation")

    def test_solution_positive_vote_no_comment(self):
        """ Test a positive review vote with no comment.

        The message that a comment is required should not be visible now.

        """
        mixer.blend('joltem.vote', voter=self.user, voteable=self.solution,
                    voter_impact=1, is_accepted=True)
        response = self.client.get(self.path)
        self.assertNotContains(response, "Votes require an explanation")

    def test_solution_negative_vote_with_comment(self):
        """ Test a negative review vote with a comment posted.

        The message that a comment is required should not be visible now.

        """
        mixer.blend('joltem.vote', voter=self.user, voteable=self.solution,
                    voter_impact=1, is_accepted=False)
        mixer.blend('joltem.comment', project=self.solution.project,
                    owner=self.user, commentable=self.solution)
        response = self.client.get(self.path)
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


class SolutionListsCaching(TestCase):

    """ Test caching in SolutionBaseListView its children. """

    def test_review_filter_caching(self):
        """ Test that filter is not being cached. """
        bill = mixer.blend('joltem.user', username='bill')
        jill = mixer.blend('joltem.user', username='jill')
        v = views.MyReviewSolutionsView()
        v.request = type("MockRequest", (object, ), dict(user=bill))
        self.assertEqual(v.filters['owner__ne'](v).username, 'bill')
        self.assertEqual(v.filters['vote_set__voter__ne'](v).username, 'bill')
        v.request.user = jill
        self.assertEqual(v.filters['owner__ne'](v).username, 'jill')
        self.assertEqual(v.filters['vote_set__voter__ne'](v).username, 'jill')


    def test_review_filter_remains_callable(self):
        """ Test that filter remains callable after getting queryset. """
        bill = mixer.blend('joltem.user', username='bill')
        v = views.MyReviewSolutionsView()
        v.project = mixer.blend('project.project')
        v.request = type("MockRequest", (object, ), dict(user=bill))
        self.assertEqual(type(v.filters['owner__ne']).__name__, 'function')
        v.get_queryset()
        self.assertEqual(type(v.filters['owner__ne']).__name__, 'function')

SOLUTION_COMMITS_URL = '/{project_id}/solution/{solution_id}/commits/'
SOLUTION_COMMITS_REPO_URL = '/{project_id}/solution/{solution_id}/commits/repository/{repo_id}/'


class SolutionCommitsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.solution = mixer.blend(
            'solution.solution',
        )

        self.url = SOLUTION_COMMITS_URL.format(
            project_id=self.solution.project.id,
            solution_id=self.solution.pk,
        )

    def test_it_is_ok_if_project_has_no_repositories(self):
        response = self.app.get(self.url, user=self.user)

        self.assertContains(response, 'The project has no repositories')

    def test_404_if_project_does_not_exist(self):
        url_with_faked_project = SOLUTION_COMMITS_URL.format(
            project_id=1000000,
            solution_id=self.solution.pk,
        )

        self.app.get(url_with_faked_project, user=self.user, status=404)

    def test_404_if_solution_does_not_exist(self):
        url_with_faked_solution = SOLUTION_COMMITS_URL.format(
            project_id=self.solution.project.id,
            solution_id=0,
        )

        self.app.get(url_with_faked_solution, user=self.user, status=404)

    def test_404_if_repository_does_not_exist(self):
        url_with_faked_repo = SOLUTION_COMMITS_REPO_URL.format(
            project_id=self.solution.project.id,
            solution_id=self.solution.pk,
            repo_id='0'
        )

        self.app.get(url_with_faked_repo, user=self.user, status=404)


MY_REVIEWED_SOLUTIONS_URL = '/{project_id}/solution/reviewed/my/'


class MyReviewedSolutionsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = MY_REVIEWED_SOLUTIONS_URL.format(
            project_id=self.project.id,
        )

    def test_user_has_two_reviewed_solutions(self):
        mixer.blend('solution.solution')

        solutions = mixer.cycle(2).blend(
            'solution.solution', project=self.project, title=mixer.RANDOM)
        for solution in solutions:
            solution.add_vote(voter=self.user, is_accepted=True)

        response = self.app.get(self.url, user=self.user, status=200)

        for solution in solutions:
            self.assertContains(response, solution.title)


MY_REVIEW_SOLUTIONS_URL = '/{project_id}/solution/review/my/'


class MyReviewSolutionsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = MY_REVIEW_SOLUTIONS_URL.format(
            project_id=self.project.id,
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


MY_INCOMPLETE_SOLUTIONS_URL = '/{project_id}/solution/incomplete/my/'


class MyIncompleteSolutionsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = MY_INCOMPLETE_SOLUTIONS_URL.format(
            project_id=self.project.id,
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


MY_COMPLETE_SOLUTIONS_URL = '/{project_id}/solution/complete/my/'


class MyCompleteSolutionsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = MY_COMPLETE_SOLUTIONS_URL.format(
            project_id=self.project.id,
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


ALL_INCOMPLETE_SOLUTIONS_URL = '/{project_id}/solution/incomplete/'


class IncompleteSolutionsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = ALL_INCOMPLETE_SOLUTIONS_URL.format(
            project_id=self.project.id,
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


ALL_COMPLETE_SOLUTIONS_URL = '/{project_id}/solution/complete/'


class CompleteSolutionsTest(WebTest, ViewTestMixin):

    def setUp(self):
        self.user = mixer.blend('joltem.user')
        self.project = mixer.blend('project.project')

        self.url = ALL_COMPLETE_SOLUTIONS_URL.format(
            project_id=self.project.id,
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
