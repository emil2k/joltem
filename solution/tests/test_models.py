from django.test import TestCase

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

    def test_magnitude_to_value(self):
        """ Test the function magnitude_to_vote_value. """
        self.assertEqual(Solution.magnitude_to_vote_value(1), 10)
        self.assertEqual(Solution.magnitude_to_vote_value(2), 100)
        self.assertEqual(Solution.magnitude_to_vote_value(3), 1000)
        self.assertEqual(Solution.magnitude_to_vote_value(4), 10000)
        self.assertEqual(Solution.magnitude_to_vote_value(5), 100000)
