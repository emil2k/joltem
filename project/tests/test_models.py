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
            overview['reviewed_tasks_count'],
            project.task_set.filter(is_reviewed=True).count(),
        )

        tasks = list(overview.get('tasks'))
        self.assertTrue(tasks[0].time_updated > tasks[-1].time_updated)
