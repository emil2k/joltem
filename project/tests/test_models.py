from django.test.testcases import TestCase
from joltem.libs import mixer

from ..models import Project


class ProjectModelTest(TestCase):

    def test_get_review(self):

        # Prepare project data
        project = mixer.blend(Project)
        tasks = mixer.cycle(2).blend('task.task', project=project)
        solutions = mixer.cycle(2).blend(
            'solution.solution', task=(t for t in tasks),
            project=mixer.mix.task.project)
        comments = mixer.cycle(2).blend(
            'joltem.comment', commentable=(s for s in solutions),
            owner=mixer.select('joltem.user'), project=project)

        overview = project.get_overview()
        self.assertEqual(set(tasks), set(overview.get('tasks')))
        self.assertEqual(set(solutions), set(overview.get('solutions')))
        self.assertEqual(set(comments), set(overview.get('comments')))

        tasks = list(overview.get('tasks'))
        self.assertTrue(tasks[0].time_updated > tasks[-1].time_updated)
