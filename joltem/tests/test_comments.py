from django.test import TestCase
from joltem.models import Comment


class CommentModelTest(TestCase):

    """ Test Comment model. """

    def test_magnitude_to_value(self):
        """ Test the function magnitude_to_vote_value. """
        self.assertEqual(Comment.magnitude_to_vote_value(1), 1)
        self.assertEqual(Comment.magnitude_to_vote_value(2), 10)
        self.assertEqual(Comment.magnitude_to_vote_value(3), 100)
        self.assertEqual(Comment.magnitude_to_vote_value(4), 1000)
        self.assertEqual(Comment.magnitude_to_vote_value(5), 10000)