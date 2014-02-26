from django.conf import settings
from django.test import TestCase
from django.utils.timezone import timedelta, now

from joltem.libs import mixer, load_model
from project import Impact
from solution.models import Solution


class SolutionTasksTest(TestCase):

    def test_archive_solutions(self):
        """ Test task that archives solutions. """
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

    def test_defaulting_solutions(self):
        """ Test task that defaults solutions impacts.

        It updates the cached impact values for the user and project specific
        impacts. Requires disabling signal to test.

        """
        from solution.tasks import review_solutions
        from django.db.models.signals import post_save
        from joltem import receivers
        expired = now() - timedelta(
            seconds=settings.SOLUTION_REVIEW_PERIOD_SECONDS + 1)
        # Disable signal to let task update cached values
        post_save.disconnect(receivers.update_project_impact_from_voteables,
                             sender=Solution)
        s = mixer.blend('solution.solution', task=mixer.RANDOM, impact=1,
                        is_completed=True, time_completed=expired)
        post_save.connect(
            receivers.update_project_impact_from_voteables, sender=Solution)
        self.assertEqual(load_model(s.owner).impact, 0)
        review_solutions.delay()
        self.assertEqual(load_model(s.owner).impact, 1)
        pi = Impact.objects.get(user_id=s.owner_id, project_id=s.project_id)
        self.assertEqual(pi.impact, 1)
