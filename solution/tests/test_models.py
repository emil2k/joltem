from django.test import TestCase
from django.core.cache import cache

from joltem.libs import mixer
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
