from django.test.testcases import TestCase
from django.utils import timezone
from datetime import timedelta
from joltem.libs import mixer
from django.conf import settings
from joltem.models import User
from joltem.tests.test_notifications import NotificationTestCase

from ..models import Project, Ratio, Impact


class ProjectModelTest(TestCase):

    """ Tests for the project model. """

    def setUp(self):
        self.project = mixer.blend(Project)

    def test_feed_order(self):
        """ Test that the feed is ordered properly. """
        old = mixer.blend('task.task', project=self.project,
                           time_updated=timezone.now() - timedelta(days=7))
        new = mixer.blend('solution.solution', project=self.project,
                           time_updated=timezone.now())
        self.assertEqual(self.project.get_feed(),
                         [new, old])

    def test_feed_includes(self):
        """ Test that the feed includes comments, tasks, and solutions. """
        tasks = mixer.cycle(4).blend(
            'task.task', project=self.project, is_reviewed=mixer.RANDOM)
        solutions = mixer.cycle(4).blend(
            'solution.solution', task=(t for t in tasks),
            project=mixer.MIX.task.project, is_completed=mixer.RANDOM)
        mixer.cycle(4).blend(
            'joltem.comment', commentable=(s for s in solutions),
            owner=mixer.SELECT('joltem.user'), project=self.project)
        self.assertEqual(len(self.project.get_feed(limit=20)), 12)

    def test_get_overview(self):
        """ Test that overview returns all the necessary components. """
        overview = self.project.get_overview()
        self.assertTrue('feed' in overview)
        self.assertTrue('completed_solutions_count' in overview)
        self.assertTrue('open_solutions_count' in overview)
        self.assertTrue('open_tasks_count' in overview)
        self.assertTrue('completed_tasks_count' in overview)


class ProjectCompletedCountTest(TestCase):

    """ Tests related to project specific completed count. """

    def setUp(self):
        self.impact = mixer.blend('project.impact')
        self.project = self.impact.project
        self.user = self.impact.user

    def test_completed_function(self):
        """ Test completed count functions. """
        s = mixer.blend('solution.solution', owner=self.user,
                        project=self.project)
        self.assertEqual(self.impact.get_completed(), 0)
        s.mark_complete(impact=1)
        self.assertEqual(self.impact.get_completed(), 1)

    def test_completed_function_other_project(self):
        """ Test other projects solutions.

        Solutions from other projects should not count towards completed
        count on a particular project.

        """
        s = mixer.blend('solution.solution', owner=self.user)
        s.mark_complete(impact=1)
        self.assertEqual(self.impact.get_completed(), 0)

    def test_completed_function_other_user(self):
        """ Test other users solutions.

        Solutions from other user should not count towards completed count
        for a particular user.

        """
        s = mixer.blend('solution', project=self.project)
        s.mark_complete(impact=1)
        self.assertEqual(self.impact.get_completed(), 0)

    def test_completed_cache(self):
        """ Test that the completed count cache updates properly. """
        reload = lambda i: Impact.objects.get(id=i.id)
        s = mixer.blend('solution.solution', owner=self.user,
                        project=self.project)
        self.assertEqual(reload(self.impact).completed, 0)
        s.mark_complete(impact=1)
        self.assertEqual(reload(self.impact).completed, 1)
        s.delete()
        self.assertEqual(reload(self.impact).completed, 0)


class ProjectCountsTest(TestCase):

    """ Tests related to calculation of various project counts. """

    def setUp(self):
        self.project = mixer.blend(Project)

    def test_open_solutions_count(self):
        """ Test open solutions count. """
        mixer.blend('solution.solution', project=self.project,
                    is_completed=False, is_closed=False)
        self.assertEqual(self.project.get_open_solutions_count(), 1)

    def test_open_solutions_count_closed(self):
        """ Test open solutions does not count closed solutions. """
        mixer.blend('solution.solution', project=self.project,
                    is_completed=False, is_closed=True)
        self.assertEqual(self.project.get_open_solutions_count(), 0)

    def test_open_solutions_count_completed(self):
        """ Test open solutions does not count completed solutions. """
        mixer.blend('solution.solution', project=self.project,
                    is_completed=True, is_closed=False)
        self.assertEqual(self.project.get_open_solutions_count(), 0)

    def test_completed_solutions_count(self):
        """ Test completed solutions count. """
        mixer.blend('solution.solution', project=self.project,
                    is_completed=True)
        self.assertEqual(self.project.get_completed_solutions_count(), 1)

    def test_completed_solutions_count_incomplete(self):
        """ Test completed solutions does not count incomplete. """
        mixer.blend('solution.solution', project=self.project,
                    is_completed=False)
        self.assertEqual(self.project.get_completed_solutions_count(), 0)

    def test_open_tasks_count(self):
        """ Test open tasks count. """
        mixer.blend('task.task', project=self.project,
                    is_closed=False, is_accepted=True)
        self.assertEqual(self.project.get_open_tasks_count(), 1)

    def test_open_tasks_count_rejected(self):
        """ Test open tasks count does not count rejected tasks. """
        mixer.blend('task.task', project=self.project,
                    is_closed=False, is_accepted=False)
        self.assertEqual(self.project.get_open_tasks_count(), 0)

    def test_open_tasks_count_closed(self):
        """ Test open tasks count does not count closed tasks. """
        mixer.blend('task.task', project=self.project,
                    is_closed=True, is_accepted=True)
        self.assertEqual(self.project.get_open_tasks_count(), 0)

    def test_completed_tasks_count(self):
        """ Test completed tasks count. """
        mixer.blend('task.task', project=self.project,
                    is_closed=True, is_accepted=True)
        self.assertEqual(self.project.get_completed_tasks_count(), 1)

    def test_completed_tasks_count_rejected(self):
        """ Test completed tasks count does not count rejected tasks. """
        mixer.blend('task.task', project=self.project,
                    is_closed=True, is_accepted=False)
        self.assertEqual(self.project.get_completed_tasks_count(), 0)

    def test_completed_tasks_count_open(self):
        """ Test completed tasks count does not count open tasks. """
        mixer.blend('task.task', project=self.project,
                    is_closed=False, is_accepted=True)
        self.assertEqual(self.project.get_completed_tasks_count(), 0)


class ProjectNotificationTest(NotificationTestCase):

    """ Test project specific notifications. """

    FROZEN_TEXT = "Your votes ratio is low, earning of impact has been " \
                  "frozen on Apple"
    UNFROZEN_TEXT = "Votes ratio raised, earning of impact has been " \
                    "unfrozen on Apple"

    def setUp(self):
        self.project = mixer.blend(Project, name="apple", title="Apple")

    def test_get_notification_url(self):
        """ Test project notification url. """
        n = mixer.blend('joltem.notification',
                        type=settings.NOTIFICATION_TYPES.frozen_ratio,
                        notifying=self.project)
        self.assertEqual(self.project.get_notification_url(n),
                         '/%d/' % self.project.id)

    def test_get_notification_text_frozen_ratio(self):
        """ Test notification text for frozen by ratio."""
        n = mixer.blend('joltem.notification',
                        type=settings.NOTIFICATION_TYPES.frozen_ratio,
                        notifying=self.project)
        self.assertEqual(self.project.get_notification_text(n),
                         self.FROZEN_TEXT)

    def test_get_notification_text_unfrozen_ratio(self):
        """ Test notification text for unfrozen by ratio."""
        n = mixer.blend('joltem.notification',
                        type=settings.NOTIFICATION_TYPES.unfrozen_ratio,
                        notifying=self.project)
        self.assertEqual(self.project.get_notification_text(n),
                         self.UNFROZEN_TEXT)

    def test_notify_frozen_ratio(self):
        """ Test notify frozen ratio working properly.

        Should update notification instead of create a new notification.

        """
        u = mixer.blend('joltem.user')
        self.project.notify_frozen_ratio(u)
        self.assertNotificationReceived(
            u, self.project, settings.NOTIFICATION_TYPES.frozen_ratio,
            self.FROZEN_TEXT)
        self.project.notify_frozen_ratio(u)  # test that it updates
        self.assertNotificationReceived(
            u, self.project, settings.NOTIFICATION_TYPES.frozen_ratio,
            self.FROZEN_TEXT)  # implies only one received

    def test_notify_unfrozen_ratio(self):
        """ Test notify unfrozen ratio working properly.

        Should update notification instead of create a new notification.

        """
        u = mixer.blend('joltem.user')
        self.project.notify_unfrozen_ratio(u)
        self.assertNotificationReceived(
            u, self.project, settings.NOTIFICATION_TYPES.unfrozen_ratio,
            self.UNFROZEN_TEXT)
        self.project.notify_unfrozen_ratio(u)  # test that it updates
        self.assertNotificationReceived(
            u, self.project, settings.NOTIFICATION_TYPES.unfrozen_ratio,
            self.UNFROZEN_TEXT)  # implies only one received


class ProjectGroupsTest(TestCase):

    """ Test project user groups. """

    def setUp(self):
        self.project = mixer.blend('project.project')
        self.user = mixer.blend('joltem.user')

    def test_is_admin(self):
        """ Test is_admin function. """
        self.project.admin_set.add(self.user)
        self.project.save()
        self.assertTrue(self.project.is_admin(self.user.id))

    def test_is_manager(self):
        """ Test is_manager function. """
        self.project.manager_set.add(self.user)
        self.project.save()
        self.assertTrue(self.project.is_manager(self.user.id))

    def test_is_developer(self):
        """ Test is_developer function. """
        self.project.developer_set.add(self.user)
        self.project.save()
        self.assertTrue(self.project.is_developer(self.user.id))


class BaseRatioModelTest(TestCase):

    """ A base for test cases dealing with the Ratio model. """

    def setUp(self):
        self.ratio = mixer.blend('project.ratio', is_frozen=False,
                                 time_frozen=None, user__username="emil")
        self.user = self.ratio.user
        self.project = self.ratio.project

    def _mock_solution(self, impact=10):
        """ Mock a solution on the project owned by the user. """
        return mixer.blend('solution.solution', owner=self.user,
                           project=self.project, impact=impact)

    def _mock_others_solution(self, n=1):
        """ Mock a solution on the project owned by someone else.

        :param n: number of solutions to mock.

        """
        m = mixer
        if n > 1:
            m = mixer.cycle(n)
        return m.blend('solution.solution', project=self.project)

    def _mock_comment(self):
        """ Mock a comment on the project owned by the user. """
        return mixer.blend('joltem.comment', owner=self.user,
                           project=self.project,
                           commentable=self._mock_solution())

    def _mock_others_comment(self):
        """ Mock a comment on the project owned by someone else. """
        return mixer.blend('joltem.comment', project=self.project,
                           commentable=self._mock_others_solution())

    #  For reloading

    def _load_user(self):
        """ Reload the test case user. """
        return User.objects.get(id=self.user.id)

    def _load_ratio(self, user=None, project=None):
        """ Reload ratio for the user on the project.

        :param user: if user is not passed, default to test case user.
        :param project: if project is not passed, default to test case project.

        """
        if not user:
            user = self.user
        if not project:
            project = self.project
        return Ratio.objects.get(project_id=project.id, user_id=user.id)

    def _load_impact(self, user=None, project=None):
        """ Reload impact for the user on the project.

        :param user: if user is not passed, default to test case user.
        :param project: if project is not passed, default to test case project.

        """
        if not user:
            user = self.user
        if not project:
            project = self.project
        return Impact.objects.get(project_id=project.id, user_id=user.id)

    def _mock_votes_out(self, n=5, add_comments=False):
        """ Mocking votes out, to prevent impact freezing.

        :param n: number of votes to mock.
        :param add_comments: whether to add comments on each solution to make
            votes valid.

        """
        s = self._mock_others_solution
        votes = mixer.cycle(n).blend(
            'joltem.vote', voteable=s,
            voter=self.user, voter_impact=100, is_accepted=True)
        if add_comments:
            mixer.cycle(n).blend('joltem.comment', project=self.project,
                                 owner=(v.voter for v in votes),
                                 commentable=(v.voteable for v in votes))

    @staticmethod
    def _mock_vote_in(voteable, magnitude=1, voter_impact=100):
        """ Mock valid vote in on voteable.

        :param voteable:
        :param magnitude:
        :param voter_impact:
        :return Vote:

        """
        return mixer.blend('joltem.vote', voteable=voteable,
                           voter_impact=voter_impact, is_accepted=magnitude > 0,
                           magnitude=magnitude)

    def _mock_valid_solution_vote_in(self, solution, is_accepted=True,
                                     voter_impact=100):
        """ Mock valid vote on a solution, by adding a comment.

        :param solution:
        :param is_accepted:
        :param voter_impact:
        :return Vote:

        """
        v = self._mock_vote_in(solution, is_accepted, voter_impact)
        if not is_accepted:
            self._mock_add_comment_for_vote(v)
        return v

    @staticmethod
    def _mock_add_comment_for_vote(*votes):
        """ Mock add comment on solution for a given vote.

        Used to make votes valid on solutions.

        :param votes:
        :return:

        """
        for vote in votes:
            mixer.blend('joltem.comment', project=vote.voteable.project,
                        owner=vote.voter, commentable=vote.voteable)


class RatioModelTest(BaseRatioModelTest):

    """ Test project vote ratio model. """

    # Freezing

    def test_update_frozen_state_equal(self):
        """ Test update frozen state with votes ratio equal to threshold. """
        self.ratio.is_frozen = True
        self.ratio.votes_ratio = Ratio.RATIO_THRESHOLD
        self.ratio.update_frozen_state()
        self.assertFalse(self.ratio.is_frozen)

    def test_update_frozen_state_above(self):
        """ Test update frozen state with votes ratio below threshold. """
        self.ratio.is_frozen = True
        self.ratio.votes_ratio = Ratio.RATIO_THRESHOLD * 2
        self.ratio.update_frozen_state()
        self.assertFalse(self.ratio.is_frozen)

    def test_update_frozen_state_below(self):
        """ Test update frozen state with votes ratio below threshold. """
        self.ratio.is_frozen = False
        self.ratio.votes_ratio = Ratio.RATIO_THRESHOLD / 2
        self.ratio.update_frozen_state()
        self.assertTrue(self.ratio.is_frozen)

    def test_update_frozen_state_infinite(self):
        """ Test update frozen state with infinite votes ratio. """
        self.ratio.is_frozen = False
        self.ratio.votes_ratio = Ratio.INFINITY
        self.ratio.update_frozen_state()
        self.assertFalse(self.ratio.is_frozen)

    def test_update_frozen_state_none(self):
        """ Test update frozen state with None votes ratio.

        Happens when there is no votes in or out.

        """
        self.ratio.is_frozen = False
        self.ratio.votes_ratio = None
        self.ratio.update_frozen_state()
        self.assertFalse(self.ratio.is_frozen)

    def test_mark_frozen(self):
        """ Test mark_frozen function. """
        self.ratio.mark_frozen()
        reloaded = self._load_ratio(self.user)
        self.assertTrue(reloaded.is_frozen)
        self.assertIsNotNone(reloaded.time_frozen)

    def test_mark_frozen_time_creep(self):
        """ Test that time_frozen isn't updated if frozen.

        Otherwise this might introduce a time_frozen creep that would
        make the field useless as each time mark_frozen the frozen time
        range would shrink.

        """
        self.ratio.mark_frozen()
        self.ratio.time_frozen = None
        self.ratio.save()
        self.ratio.mark_frozen()
        reloaded = self._load_ratio(self.user)
        self.assertIsNone(reloaded.time_frozen)

    def test_mark_unfrozen(self):
        """ Test mark_unfrozen function. """
        self.ratio.mark_unfrozen()
        reloaded = self._load_ratio(self.user)
        self.assertFalse(reloaded.is_frozen)
        self.assertIsNone(reloaded.time_frozen)

    # No votes

    def test_no_votes(self):
        """ Test vote in and out functions with no votes. """
        self.assertEqual(self.ratio.get_votes_in(), 0)
        self.assertEqual(self.ratio.get_votes_out(), 0)

    # Votes in metric

    def test_votes_in(self):
        """ Test calculation of votes in metric. """
        s = self._mock_solution()
        votes = mixer.cycle(5).blend('joltem.vote', voteable=s, voter_impact=1)
        self._mock_add_comment_for_vote(*votes)
        self.assertEqual(self.ratio.get_votes_in(), 5)

    def test_votes_in_cap(self):
        """ Test votes in cap.

        Beyond fifth vote doesn't count.

        """
        s = self._mock_solution()
        votes = mixer.cycle(10).blend(
            'joltem.vote', voteable=s, voter_impact=1)
        self._mock_add_comment_for_vote(*votes)
        self.assertEqual(self.ratio.get_votes_in(), 5)

    def test_votes_in_others(self):
        """ Test that votes on other's solutions don't count. """
        s = self._mock_others_solution()
        mixer.blend('joltem.vote', voteable=s, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_in(), 0)

    def test_votes_in_no_impact(self):
        """ Test that voters with no impact don't count. """
        s = self._mock_solution()
        mixer.blend('joltem.vote', voteable=s, voter_impact=0)
        self.assertEqual(self.ratio.get_votes_in(), 0)

    def test_votes_in_other_projects(self):
        """ Test that votes in on other projects, don't count on votes in.

        Setup a solution on another project owned by the user, then get
        a vote on it.

        """
        s = mixer.blend('solution.solution', owner=self.user)
        self.assertEqual(s.owner_id, self.user.id)
        v = mixer.blend('joltem.vote', voteable=s, voter_impact=1)
        self._mock_add_comment_for_vote(v)
        self.assertEqual(self.ratio.get_votes_in(), 0)
        # load ratio from other project
        self.assertEqual(self._load_ratio(project=s.project).get_votes_in(), 1)

    # Votes out metric

    def test_votes_out(self):
        """ Test calculation of votes out metric. """
        s = self._mock_others_solution()
        votes = mixer.cycle(4).blend('joltem.vote', voteable=s, voter_impact=1)
        v = mixer.blend('joltem.vote', voteable=s, voter=self.user,
                        voter_impact=1)
        self._mock_add_comment_for_vote(v, *votes)
        self.assertEqual(self.ratio.get_votes_out(), 1)

    def test_votes_out_cap(self):
        """ Test votes out cap.

        Beyond fifth doesn't count.

        """
        s = self._mock_others_solution()
        mixer.cycle(5).blend('joltem.vote', voteable=s, voter_impact=1)
        mixer.blend('joltem.vote', voteable=s, voter=self.user, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_out(), 0)

    def test_votes_out_no_impact(self):
        """ Test that votes with no impact, don't count towards votes out. """
        s = self._mock_others_solution()
        mixer.blend('joltem.vote', voteable=s, voter=self.user, voter_impact=0)
        self.assertEqual(self.ratio.get_votes_out(), 0)

    def test_votes_out_other_projects(self):
        """ Test that votes on other projects, don't count on votes_out.

        Setup a solution that is on another project and owned by someone
        else then cast a vote on it.

        """
        s = mixer.blend('solution.solution')
        v = mixer.blend('joltem.vote', voteable=s,
                        voter=self.user, voter_impact=1)
        self._mock_add_comment_for_vote(v)
        self.assertEqual(self.ratio.get_votes_out(), 0)
        # load ratio from other project
        self.assertEqual(self._load_ratio(project=s.project)
                         .get_votes_out(), 1)

    # Votes ratio metric

    def test_votes_ratio_no_votes(self):
        """ Test votes ratio metric with no votes.

        If there is no votes it should return None.

        """
        self.assertEqual(self.ratio.get_votes_ratio(), None)

    def test_votes_ratio_min(self):
        """ Test votes ratio at minimum value. """
        s = self._mock_solution()
        v = mixer.blend('joltem.vote', voteable=s, voter_impact=1)
        self._mock_add_comment_for_vote(v)
        self.assertEqual(self.ratio.get_votes_ratio(), 0.0)

    def test_votes_ratio_max(self):
        """ Test votes ratio at maximum value.

        When there is votes out and no votes in the vote ratio, should
        technically be infinity. Infinity is represented by -1.0 or the
        constant INFINITY in the Ratio model.

        """
        s = self._mock_others_solution()
        v = mixer.blend('joltem.vote', voteable=s,
                        voter=self.user, voter_impact=1)
        self._mock_add_comment_for_vote(v)
        self.assertEqual(self.ratio.get_votes_ratio(), Ratio.INFINITY)

    def test_votes_ratio_float(self):
        """ Test votes ratio returns a float. """
        s = self._mock_solution()
        votes = mixer.cycle(4).blend(
            'joltem.vote', voteable=s, voter_impact=1)  # in
        o = self._mock_others_solution
        votes += mixer.cycle(
            3).blend('joltem.vote', voter=self.user, voteable=o,
                     voter_impact=1)  # out
        self._mock_add_comment_for_vote(*votes)
        self.assertEqual(self.ratio.get_votes_ratio(), 0.75)

    # Signals and receivers

    def test_signal_receiver(self):
        """ Testing signals, voter ratio metrics should update. """
        s = self._mock_solution()
        v = mixer.blend('joltem.vote', voteable=s, voter_impact=1)
        self._mock_add_comment_for_vote(v)
        self.assertEqual(self._load_ratio(self.user).get_votes_in(), 1)
        self.assertEqual(self._load_ratio(v.voter).get_votes_out(), 1)
        v.delete()
        self.assertEqual(self._load_ratio(self.user).get_votes_ratio(), None)
        self.assertEqual(self._load_ratio(v.voter).get_votes_ratio(), None)


class VoteRatioSolutionFreezeTest(BaseRatioModelTest):

    """ Tests freeze and unfreeze for solutions. """

    def setUp(self):
        super(VoteRatioSolutionFreezeTest, self).setUp()
        self.old = self._mock_solution(impact=10)
        self.old.is_completed = True
        self.old.time_completed = timezone.now() - timedelta(days=7)
        self.old.time_posted = timezone.now() - timedelta(days=10)
        self.old.save()
        self.new = self._mock_solution(impact=10)
        self.new.is_completed = True
        self.new.time_completed = timezone.now() + timedelta(days=7)
        self.new.time_posted = timezone.now() + timedelta(days=10)
        self.new.save()

    def test_freeze_impact_solutions(self):
        """ Test freezing of impact on solutions. """
        self._mock_votes_out(3, True)
        self._mock_valid_solution_vote_in(self.old)
        self._mock_valid_solution_vote_in(self.new)
        self.assertEqual(self._load_user().impact, 20)
        self.assertEqual(self._load_impact().frozen_impact, 0)
        self.ratio.mark_frozen()
        self.assertEqual(self._load_user().impact, 10)
        self.assertEqual(self._load_impact().frozen_impact, 10)

    def test_unfreeze_impact_solutions(self):
        """ Test unfreezing of impact on solutions. """
        # add some complete solutions so that threshold is possible
        for s in self._mock_others_solution(2):
            s.mark_complete(5)
        self._mock_valid_solution_vote_in(self.old)
        self._mock_valid_solution_vote_in(self.new)
        self.assertTrue(self._load_ratio().is_frozen)
        self.assertEqual(self._load_user().impact, 10)
        self.assertEqual(self._load_impact().frozen_impact, 10)
        self._mock_votes_out(2, True)
        self.assertFalse(self._load_ratio().is_frozen)
        self.assertEqual(self._load_user().impact, 20)
        self.assertEqual(self._load_impact().frozen_impact, 0)


class VoteRatioPossibilityTest(BaseRatioModelTest):

    """ Tests votes ratio possible range. """

    def test_max_out_no_solutions(self):
        """ Test max out with no solutions. """
        self.assertEqual(self.ratio.maximum_possible_votes_out(), 0)

    def test_max_out_incomplete(self):
        """ Test max out with an incomplete solution.

        Incomplete solution should not count, because it cannot be voted on.

        """
        s = self._mock_others_solution()
        s.mark_incomplete()
        self.assertEqual(self.ratio.maximum_possible_votes_out(), 0)

    def test_max_out_complete(self):
        """ Test max out with completed solution. """
        s = self._mock_others_solution()
        s.mark_complete(5)
        self.assertEqual(self.ratio.maximum_possible_votes_out(), 1)

    def test_max_out_own_solution(self):
        """ Test max out, that own solution does not count. """
        s = self._mock_solution()
        s.mark_complete(5)
        self.assertEqual(self.ratio.maximum_possible_votes_out(), 0)

    def test_max_out_voted_valid(self):
        """ Test max out, already have valid vote on.

        If the user already has a valid vote it should count in max out.

        """
        s = self._mock_others_solution()
        s.mark_complete(5)
        votes = mixer.cycle(Ratio.VOTES_THRESHOLD - 1).blend(
            'joltem.vote', voteable=s, voter_impact=1, magnitude=1,
            is_accepted=True)
        self._mock_add_comment_for_vote(*votes)
        user_vote = mixer.blend(
            'joltem.vote', voter=self.user, voteable=s, voter_impact=1,
            magnitude=1, is_accepted=True)
        self._mock_add_comment_for_vote(user_vote)
        vote = mixer.blend(
            'joltem.vote', voteable=s, voter_impact=1, magnitude=1,
            is_accepted=True)
        self._mock_add_comment_for_vote(vote)
        self.assertEqual(self.ratio.maximum_possible_votes_out(), 1)

    def test_possible(self):
        """ Test when votes ratio threshold possible. """
        self._mock_others_solution().mark_complete(5)
        s = self._mock_solution()
        self._mock_valid_solution_vote_in(s)
        self.assertTrue(self.ratio.is_threshold_possible())

    def test_impossible(self):
        """ Test when votes ratio threshold impossible. """
        s = self._mock_solution()
        self._mock_valid_solution_vote_in(s)
        self.assertFalse(self.ratio.is_threshold_possible())
