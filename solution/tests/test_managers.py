# coding: utf-8
from django.test import TestCase

from joltem.libs import mixer

from ..models import Solution


class ReviewedByUserTest(TestCase):

    def test_get_solution_only_voted_by_given_user_from_two_solutions(self):
        mixer.blend('solution.solution')
        solution = mixer.blend('solution.solution')

        user = mixer.blend('joltem.user')
        solution.add_vote(voter=user, vote_magnitude=1)

        expected_solution = Solution.objects.reviewed_by_user(user).get()

        self.assertEqual(solution, expected_solution)

    def test_empty_qs_when_there_is_no_solution_voted_by_given_user(self):
        mixer.blend('solution.solution')
        solution = mixer.blend('solution.solution')

        bob = mixer.blend('joltem.user')
        jon = mixer.blend('joltem.user')
        solution.add_vote(voter=bob, vote_magnitude=1)

        expected_solution_qty = 0

        self.assertEqual(
            Solution.objects.reviewed_by_user(jon).count(),
            expected_solution_qty
        )

    def test_there_is_only_one_db_query_to_get_reviewed_solutions(self):
        solution = mixer.blend('solution.solution')

        user = mixer.blend('joltem.user')
        solution.add_vote(voter=user, vote_magnitude=1)

        # "step" parameter of slice syntax is used to evaluate QuerySet.
        with self.assertNumQueries(1):
            Solution.objects.reviewed_by_user(user)[::1]
