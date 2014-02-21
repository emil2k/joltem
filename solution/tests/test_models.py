from django.test import TestCase
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from joltem.libs import mixer, load_model
from solution.models import Solution


class SolutionModelTest(TestCase):

    """ Tests for the Solution model. """

    def setUp(self):
        self.solution = mixer.blend('solution.solution')
        self.project = self.solution.project

    def _mock_comment(self, commentator=None):
        """ Mock a comment on the solution. """
        if not commentator:
            commentator = mixer.blend('joltem.user')
        c = mixer.blend('joltem.comment', commentable=self.solution,
                        project=self.project, owner=commentator)
        return c

    def test_has_commented(self):
        """ Test the has_commented function.

        Make sure that comments by others don't cause this function to
        give a false positive.

        """
        commentator = mixer.blend('joltem.user')
        self._mock_comment()  # comment by another user
        self.assertFalse(self.solution.has_commented(commentator.id))
        self._mock_comment(commentator)
        self.assertTrue(self.solution.has_commented(commentator.id))

    def test_mark_complete(self):
        """ Test the mark_complete function.

        Should set the demanded impact, set the is_completed boolean,
        timestamp, and save.

        """
        self.solution.mark_complete(5)
        loaded = Solution.objects.get(id=self.solution.id)
        self.assertEqual(loaded.impact, 5)
        self.assertTrue(loaded.is_completed)
        self.assertIsNotNone(loaded.time_completed)

    def test_mark_incomplete(self):
        """ Test the mark_incomplete function. """
        self.solution.mark_complete(5)
        self.solution.mark_incomplete()
        loaded = Solution.objects.get(id=self.solution.id)
        self.assertEqual(loaded.impact, None)
        self.assertFalse(loaded.is_completed)
        self.assertIsNone(loaded.time_completed)

    def test_mark_incomplete_clear_votes(self):
        """ Test that mark_incomplete clears votes. """
        self.solution.mark_complete(5)
        mixer.cycle(3).blend('joltem.vote', voteable=self.solution)
        self.assertEqual(self.solution.vote_set.count(), 3)
        self.solution.mark_incomplete()
        self.assertEqual(self.solution.vote_set.count(), 0)

    def test_invalidate_cache(self):
        cache.set('%s:solutions_tabs' % self.project.pk, True)
        mixer.blend('solution', project=self.project)
        self.assertFalse(cache.get('%s:solutions_tabs' % self.project.pk))


class SolutionImpactDefaultingTest(TestCase):

    """ Test a solutions impact defaulting. """

    def setUp(self):
        self.solution = mixer.blend('solution.solution')
        self.solution.mark_complete(1)

    @property
    def _expired(self):
        """ Return and expired time, at which point impact should default. """
        return timezone.now() - timezone.timedelta(
            seconds=settings.SOLUTION_REVIEW_PERIOD_SECONDS + 1)

    def test_valid_vote_count(self):
        """ Test the valid vote count function.

        A rejected vote requires a comment to be considered valid.

        """
        self.assertEqual(self.solution.valid_vote_count, 0)
        bill = mixer.blend('joltem.user')
        self.solution.put_vote(bill, False)
        self.assertEqual(self.solution.valid_vote_count, 0)
        self.solution.add_comment(bill, "Not good.")
        self.assertEqual(self.solution.valid_vote_count, 1)

    def test_defaulting(self):
        """ Test that impact defaults to demanded. """
        self.assertEqual(self.solution.get_impact(), 0)
        self.solution.time_completed = self._expired
        self.solution.save()
        self.assertEqual(self.solution.get_impact(), 1)

    def test_votes_counting(self):
        """ Test expired with votes. """
        bill = mixer.blend('joltem.user')
        self.solution.put_vote(bill, False)
        self.solution.add_comment(bill, "Not good.")
        self.solution.time_completed = self._expired
        self.solution.save()
        self.assertEqual(self.solution.get_impact(), 0)