from django.test.testcases import TestCase
from django.utils import timezone
from datetime import timedelta
from joltem.libs import mixer
from joltem.models import User

from ..models import Project, Ratio


class ProjectModelTest(TestCase):

    def test_get_review(self):

        # Prepare project data
        project = mixer.blend(Project)

        tasks = mixer.cycle(4).blend(
            'task.task', project=project, is_reviewed=mixer.random)

        solutions = mixer.cycle(4).blend(
            'solution.solution', task=(t for t in tasks),
            project=mixer.mix.task.project, is_completed=mixer.random)

        comments = mixer.cycle(4).blend(
            'joltem.comment', commentable=(s for s in solutions),
            owner=mixer.select('joltem.user'), project=project)

        overview = project.get_overview()
        self.assertEqual(set(tasks), set(overview.get('tasks')))
        self.assertEqual(set(solutions), set(overview.get('solutions')))
        self.assertEqual(set(comments), set(overview.get('comments')))
        self.assertEqual(
            overview['completed_solutions_count'],
            project.solution_set.filter(is_completed=True).count(),
        )
        self.assertEqual(
            overview['completed_tasks_count'],
            project.task_set.filter(is_closed=True, is_accepted=True).count(),
        )

        tasks = list(overview.get('tasks'))
        self.assertTrue(tasks[0].time_updated > tasks[-1].time_updated)


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


class RatioModelTest(TestCase):

    """ Test project vote ratio model. """

    def setUp(self):
        self.ratio = mixer.blend('project.ratio')
        self.user = self.ratio.user
        self.project = self.ratio.project

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

    def _mock_solution(self):
        """ Mock a solution on the project owned by the user. """
        return mixer.blend('solution.solution', owner=self.user,
                           project=self.project)

    def _mock_others_solution(self):
        """ Mock a solution on the project owned by someone else. """
        return mixer.blend('solution.solution', project=self.project)

    def _mock_comment(self):
        """ Mock a comment on the project owned by the user. """
        return mixer.blend('joltem.comment', owner=self.user,
                           project=self.project,
                           commentable=self._mock_solution())

    def _mock_others_comment(self):
        """ Mock a comment on the project owned by someone else. """
        return mixer.blend('joltem.comment', project=self.project,
                           commentable=self._mock_others_solution())

    def test_votes_in(self):
        """ Test calculation of votes in metric. """
        s = self._mock_solution()
        mixer.cycle(5).blend('joltem.vote', voteable=s, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_in(), 5)

    def test_votes_in_cap(self):
        """ Test votes in cap.

        Beyond fifth vote doesn't count.

        """
        s = self._mock_solution()
        mixer.cycle(10).blend('joltem.vote', voteable=s, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_in(), 5)

    def test_votes_in_others(self):
        """ Test that votes on other's solutions don't count. """
        s = self._mock_others_solution()
        mixer.blend('joltem.vote', voteable=s, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_in(), 0)

    def test_votes_in_comments(self):
        """ Test that votes on comments don't count. """
        c = self._mock_comment()
        mixer.blend('joltem.vote', voteable=c, voter_impact=1)
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
        mixer.blend('joltem.vote', voteable=s, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_in(), 0)
        # load ratio from other project
        r = Ratio.objects.get(project_id=s.project_id,
                              user_id=self.user.id)
        self.assertEqual(r.get_votes_in(), 1)

    # Votes out metric

    def test_votes_out(self):
        """ Test calculation of votes out metric. """
        s = self._mock_others_solution()
        mixer.cycle(4).blend('joltem.vote', voteable=s, voter_impact=1)
        mixer.blend('joltem.vote', voteable=s, voter=self.user,
                    voter_impact=1)
        self.assertEqual(self.ratio.get_votes_out(), 1)

    def test_votes_out_cap(self):
        """ Test votes out cap.

        Beyond fifth doesn't count.

        """
        s = self._mock_others_solution()
        mixer.cycle(5).blend('joltem.vote', voteable=s, voter_impact=1)
        mixer.blend('joltem.vote', voteable=s, voter=self.user, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_out(), 0)

    def test_votes_out_comments(self):
        """ Test that votes on comments don't count towards votes out. """
        c = self._mock_others_comment()
        mixer.blend('joltem.vote', voteable=c, voter=self.user, voter_impact=1)
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
        mixer.blend('joltem.vote', voteable=s, voter=self.user, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_out(), 0)
        # load ratio from other project
        r = Ratio.objects.get(project_id=s.project_id,
                              user_id=self.user.id)
        self.assertEqual(r.get_votes_out(), 1)

    # Votes ratio metric

    def test_votes_ratio_no_votes(self):
        """ Test votes ratio metric with no votes.

        If there is no votes it should return None.

        """
        self.assertEqual(self.ratio.get_votes_ratio(), None)

    def test_votes_ratio_min(self):
        """ Test votes ratio at minimum value. """
        s = self._mock_solution()
        mixer.blend('joltem.vote', voteable=s, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_ratio(), 0.0)


    def test_votes_ratio_max(self):
        """ Test votes ratio at maximum value.

        When there is votes out and no votes in the vote ratio, should
        technically be infinity. Infinity is represented by -1.0 or the
        constant INFINITY in the Ratio model.

        """
        s = self._mock_others_solution()
        mixer.blend('joltem.vote', voteable=s, voter=self.user, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_ratio(), Ratio.INFINITY)

    def test_votes_ratio_float(self):
        """ Test votes ratio returns a float. """
        s = self._mock_solution()
        mixer.cycle(4).blend('joltem.vote', voteable=s, voter_impact=1) # in
        o = lambda : self._mock_others_solution()
        mixer.cycle(3).blend('joltem.vote', voter=self.user, voteable=o,
                             voter_impact=1) # out
        self.assertEqual(self.ratio.get_votes_ratio(), 0.75)

    # Signals and receivers

    def _load_ratio(self, user):
        """ Load ratio instance for the user on the test project.

        :return Ratio:

        """
        return Ratio.objects.get(project_id=self.project.id, user_id=user.id)

    def test_signal_receiver(self):
        """ Testing signals, voter ratio metrics should update. """
        s = self._mock_solution()
        v = mixer.blend('joltem.vote', voteable=s, voter_impact=1)
        self.assertEqual(self._load_ratio(self.user).get_votes_in(), 1)
        self.assertEqual(self._load_ratio(v.voter).get_votes_out(), 1)
        v.delete()
        self.assertEqual(self._load_ratio(self.user).get_votes_ratio(), None)
        self.assertEqual(self._load_ratio(v.voter).get_votes_ratio(), None)


class VoteRatioFreezeTest(TestCase):

    """ Tests for when impact is frozen and unfrozen due to vote ratio. """

    def setUp(self):
        self.ratio = mixer.blend('project.ratio', is_frozen=False,
                                 time_frozen=None, user__username="emil")
        self.user = self.ratio.user
        self.project = self.ratio.project

    def _load_user(self):
        """ Reload user. """
        return User.objects.get(id=self.user.id)

    def _load_ratio(self):
        """ Reload ratio. """
        return Ratio.objects.get(project_id=self.project.id,
                                 user_id=self.user.id)

    def _mock_votes_out(self, n=5):
        """ Mocking votes out, to prevent impact freezing.

        :param n: number of votes to mock.

        """
        s = lambda : mixer.blend('solution.solution', project=self.project)
        mixer.cycle(n).blend(
            'joltem.vote', voteable=s,
            voter=self.user, voter_impact=100, is_accepted=True, magnitude=1)

    def _mock_vote_in(self, voteable, magnitude=1, voter_impact=100):
        """ Mock vote in on voteable.

        :param voteable:
        :param magnitude:
        :param voter_impact:
        :return:

        """
        mixer.blend('joltem.vote', voteable=voteable, voter_impact=voter_impact,
                    is_accepted=magnitude > 0, magnitude=magnitude)

class VoteRatioSolutionFreezeTest(VoteRatioFreezeTest):

    """ Tests freeze and unfreeze for solutions. """

    def setUp(self):
        super(VoteRatioSolutionFreezeTest, self).setUp()
        self.old = mixer.blend(
            'solution.solution', owner=self.user, project=self.project,
            is_completed=True, time_completed=timezone.now()-timedelta(days=7),
            time_posted=timezone.now()-timedelta(days=10)
        )
        self.new = mixer.blend(
            'solution.solution', owner=self.user, project=self.project,
            is_completed=True, time_completed=timezone.now()+timedelta(days=7),
            time_posted=timezone.now()+timedelta(days=10)
        )

    def test_freeze_impact_solutions(self):
        """ Test freezing of impact on solutions. """
        self._mock_votes_out(3)
        self._mock_vote_in(self.old)
        self._mock_vote_in(self.new)
        u = self._load_user()
        self.assertEqual(u.impact, 20)
        self.ratio.mark_frozen()
        u = self._load_user()
        self.assertEqual(u.impact, 10)

    def test_unfreeze_impact_solutions(self):
        """ Test unfreezing of impact on solutions. """
        self._mock_vote_in(self.old)
        self._mock_vote_in(self.new)
        r = self._load_ratio()
        self.assertTrue(r.is_frozen)
        u = self._load_user()
        self.assertEqual(u.impact, 10)
        self._mock_votes_out(2)
        r = self._load_ratio()
        self.assertFalse(r.is_frozen)
        u = self._load_user()
        self.assertEqual(u.impact, 20)


class VoteRatioCommentFreezeTest(VoteRatioFreezeTest):

    """ Tests freeze and unfreeze for comment. """

    def setUp(self):
        super(VoteRatioCommentFreezeTest, self).setUp()
        commentable = lambda : mixer.blend('solution.solution',
                                           project=self.project)
        self.old = mixer.blend(
            'joltem.comment', owner=self.user, commentable=commentable,
            time_commented=timezone.now()-timedelta(days=10),
            project=self.project
        )
        self.new = mixer.blend(
            'joltem.comment', owner=self.user, commentable=commentable,
            time_commented=timezone.now()+timedelta(days=10),
            project=self.project
        )

    def test_freeze_impact_comments(self):
        """ Test freezing of impact on comments. """
        self._mock_votes_out(3)
        self._mock_vote_in(self.old)
        self._mock_vote_in(self.new)
        u = self._load_user()
        self.assertEqual(u.impact, 20)
        self.ratio.mark_frozen()
        u = self._load_user()
        self.assertEqual(u.impact, 10)

    def test_unfreeze_impact_comments(self):
        """ Test unfreezing of impact earned on comments.

        Since votes on comments don't count towards votes_in, an old
        solution is setup to take a vote and freeze the users impact.

        Then the user casts one vote to get the ratio back to 1, to
        unfreeze the impact earned on the new comment.

        "New" and "old" here refers to either after or before time of
        freezing.

        """
        self._mock_vote_in(self.old)
        self._mock_vote_in(self.new)
        # add vote on solution to freeze impact
        old_solution = mixer.blend(
            'solution.solution', owner=self.user, project=self.project,
            is_completed=True, time_completed=timezone.now()-timedelta(days=7),
            time_posted=timezone.now()-timedelta(days=10)
        )
        self._mock_vote_in(old_solution)
        r = self._load_ratio()
        self.assertTrue(r.is_frozen)
        u = self._load_user()
        self.assertEqual(u.impact, 20)
        self._mock_votes_out(1)
        r = self._load_ratio()
        self.assertFalse(r.is_frozen)
        u = self._load_user()
        self.assertEqual(u.impact, 30)