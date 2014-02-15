from django.conf import settings
from django.test import TestCase
from django.utils.timezone import timedelta, now

from joltem.libs import mixer, load_models
from solution.models import Solution


class SolutionTasksTest(TestCase):

    def test_archive_solutions(self):
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

    def test_review_automatically(self):
        NOW = now()
        frontier = NOW - timedelta(
            seconds=settings.SOLUTION_REVIEW_PERIOD_SECONDS + 300)

        s1 = mixer.blend(
            'solution.solution', task=mixer.RANDOM, time_completed=NOW,
            is_completed=True)
        s2 = mixer.blend(
            'solution.solution', task=mixer.RANDOM, time_completed=frontier,
            is_completed=True)
        s3 = mixer.blend(
            'solution.solution', task=mixer.RANDOM, time_completed=frontier,
            is_completed=True)

        s3.add_vote(mixer.blend('user'), True)

        from solution.tasks import review_solutions
        review_solutions.delay()

        s1, s2, s3 = load_models(s1, s2, s3)
        self.assertFalse(s1.is_closed)
        self.assertFalse(s3.is_closed)
        self.assertTrue(s2.is_closed)
