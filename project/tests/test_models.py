from django.test.testcases import TestCase
from joltem.libs import mixer

from ..models import Project


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


class VoteRatioModelTest(TestCase):

    """ Test project vote ratio model. """

    def setUp(self):
        self.ratio = mixer.blend('project.ratio')
        self.user = self.ratio.user
        self.project = self.ratio.project

    def test_no_votes(self):
        """ Test vote ratio functions with no votes. """
        self.assertEqual(self.ratio.get_votes_in(), 0)
        self.assertEqual(self.ratio.get_votes_out(), 0)
        self.assertEqual(self.ratio.get_votes_ratio(), None)

    # Votes in metric

    def test_votes_in(self):
        """ Test calculation of votes in metric. """
        s = mixer.blend('solution.solution', owner=self.user)
        mixer.cycle(5).blend('joltem.vote', voteable=s, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_in(), 5)

    def test_votes_in_cap(self):
        """ Test votes in cap.

        Beyond fifth vote doesn't count.

        """
        s = mixer.blend('solution.solution', owner=self.user)
        mixer.cycle(10).blend('joltem.vote', voteable=s, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_in(), 5)

    def test_votes_in_others(self):
        """ Test that votes on other's solutions don't count. """
        s = lambda : mixer.blend('solution.solution', project=self.project)
        mixer.blend('joltem.vote', voteable=s, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_in(), 0)

    def test_votes_in_comments(self):
        """ Test that votes on comments don't count. """
        c = lambda : mixer.blend('joltem.comment', project=self.project,
                                 commentable=mixer.blend('solution.solution'))
        mixer.blend('joltem.vote', voteable=c, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_in(), 0)

    def test_votes_in_no_impact(self):
        """ Test that voters with no impact don't count. """
        s = lambda : mixer.blend('solution.solution', project=self.project)
        mixer.blend('joltem.vote', voteable=s, voter_impact=0)
        self.assertEqual(self.ratio.get_votes_in(), 0)

    # Votes out metric

    def test_votes_out(self):
        """ Test calculation of votes out metric. """
        s = mixer.blend('solution.solution')
        mixer.cycle(4).blend('joltem.vote', voteable=s, voter_impact=1)
        mixer.blend('joltem.vote', voteable=s, voter=self.user,
                    voter_impact=1)
        self.assertEqual(self.ratio.get_votes_out(), 1)

    def test_votes_out_cap(self):
        """ Test votes out cap.

        Beyond fifth doesn't count.

        """
        s = mixer.blend('solution.solution')
        mixer.cycle(5).blend('joltem.vote', voteable=s, voter_impact=1)
        mixer.blend('joltem.vote', voteable=s, voter=self.user, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_out(), 0)

    def test_votes_out_comments(self):
        """ Test that votes on comments don't count towards votes out. """
        c = mixer.blend('joltem.comment',
                        commentable=mixer.blend('solution.solution'))
        mixer.blend('joltem.vote', voteable=c, voter=self.user, voter_impact=1)
        self.assertEqual(self.ratio.get_votes_out(), 0)

    def test_votes_out_no_impact(self):
        """ Test that votes with no impact, don't count towards votes out. """
        s = mixer.blend('solution.solution')
        mixer.blend('joltem.vote', voteable=s, voter=self.user, voter_impact=0)
        self.assertEqual(self.ratio.get_votes_out(), 0)


    # todo test vote ratio metric