# coding: utf-8
from django.test import TestCase

from joltem.libs import mixer

from ..models import Solution


class SolutionsReviewedByUserTest(TestCase):

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


class SolutionsNeedReviewFromUserTest(TestCase):

    def test_solution_has_not_been_reviewed_by_user_yet(self):
        solution = mixer.blend(
            'solution.solution',
            is_completed=True,
            is_closed=False,
        )

        bob = mixer.blend('joltem.user')
        jon = mixer.blend('joltem.user')
        solution.add_vote(voter=bob, vote_magnitude=1)

        expected_solution = Solution.objects.need_review_from_user(jon).get()

        self.assertEqual(solution, expected_solution)

    def test_empty_qs_when_there_is_no_completed_solution(self):
        jon = mixer.blend('joltem.user')
        mixer.blend(
            'solution.solution',
            is_completed=False,
        )

        expected_solution_qty = 0

        self.assertEqual(
            Solution.objects.need_review_from_user(jon).count(),
            expected_solution_qty
        )

    def test_empty_qs_when_there_is_no_open_solution(self):
        jon = mixer.blend('joltem.user')
        mixer.blend(
            'solution.solution',
            is_completed=True,
            is_closed=True,
        )

        expected_solution_qty = 0

        self.assertEqual(
            Solution.objects.need_review_from_user(jon).count(),
            expected_solution_qty
        )

    def test_empty_qs_when_solution_has_already_been_reviewed_by_user(self):
        solution = mixer.blend(
            'solution.solution',
            is_completed=True,
            is_closed=False,
        )

        jon = mixer.blend('joltem.user')
        solution.add_vote(voter=jon, vote_magnitude=1)

        expected_solution_qty = 0

        self.assertEqual(
            Solution.objects.need_review_from_user(jon).count(),
            expected_solution_qty
        )

    def test_empty_qs_when_user_is_owner_of_solution(self):
        jon = mixer.blend('joltem.user')
        mixer.blend(
            'solution.solution',
            is_completed=True,
            is_closed=False,
            owner=jon,
        )

        expected_solution_qty = 0

        self.assertEqual(
            Solution.objects.need_review_from_user(jon).count(),
            expected_solution_qty
        )
