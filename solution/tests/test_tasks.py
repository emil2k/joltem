from django.test import TestCase
from joltem.libs import mixer
from solution.models import Solution


class SolutionTasksTest(TestCase):

    def test_archive_solutions(self):
        from django.utils.timezone import timedelta, now
        from django.conf import settings

        NOW = now()
        frontier = NOW - timedelta(
            seconds=settings.SOLUTION_LIFE_PERIOD_SECONDS + 300)

        s1 = mixer.blend(
            'solution.solution', task=mixer.RANDOM, time_completed=NOW)
        s2 = mixer.blend(
            'solution.solution', task=mixer.RANDOM, time_completed=frontier)
        s3 = mixer.blend(
            'solution.solution', task=mixer.RANDOM, time_completed=frontier)
        self.assertFalse(s1.is_archived)
        self.assertFalse(s2.is_archived)
        self.assertFalse(s3.is_archived)

        from solution.tasks import archive_solutions
        archive_solutions.delay()
        s1, s2, s3 = Solution.objects.all()
        self.assertFalse(s1.is_archived)
        self.assertTrue(s2.is_archived)
        self.assertTrue(s3.is_archived)

        self.assertTrue(s2.owner.notification_set.all())
        self.assertTrue(s3.owner.notification_set.all())
        notify = s2.owner.notification_set.get()
        self.assertEqual(
            notify.get_text(), 'Solution "%s" was archived' % s2.default_title)
