from django.test.testcases import TestCase
from django.utils import timezone
from datetime import timedelta
from joltem.libs import mixer

from ..models import Project, Impact


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
        _reload = lambda i: Impact.objects.get(id=i.id)
        s = mixer.blend('solution.solution', owner=self.user,
                        project=self.project)
        self.assertEqual(_reload(self.impact).completed, 0)
        s.mark_complete(impact=1)
        self.assertEqual(_reload(self.impact).completed, 1)
        s.delete()
        self.assertEqual(_reload(self.impact).completed, 0)


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