""" Solution related tests. """
from django.test import TestCase

from joltem.libs import mixer, load_model
from joltem.libs.mock.models import (
    get_mock_user, get_mock_project, get_mock_task, get_mock_solution,
    load_project_impact)
from joltem.models.votes import VOTEABLE_THRESHOLD
from project.models import Impact


class PermissionsTestCase(TestCase):

    """ Test solution permissions.  """

    def setUp(self):
        """ Create project and four mock users. Jill is an admin. """
        self.jill = get_mock_user('jill')  # the project admin
        self.abby = get_mock_user('abby')
        self.bob = get_mock_user('bob')
        self.zack = get_mock_user('zack')
        # Setup project, make Jill admin
        self.project = get_mock_project("Hover")
        self.project.admin_set.add(self.jill)
        self.project.save()

    def test_is_owner(self):
        """ Test solution ownership. """
        t = get_mock_task(self.project, self.bob,
                          is_reviewed=True, is_accepted=True)
        s = get_mock_solution(self.project, self.zack, t)

        self.assertFalse(s.is_owner(self.jill))
        self.assertFalse(s.is_owner(self.bob))
        self.assertTrue(s.is_owner(self.zack))


class ImpactTestCase(TestCase):

    """ Test solution impact determination. """

    # Custom assertions

    def assertImpactEqual(self, user, expected):
        """ Assert user's total impact. """
        self.assertEqual(user.impact, expected)

    def assertCompletedEqual(self, user, expected):
        """ Assert user's completed solutions count. """
        self.assertEqual(user.completed, expected)

    def assertProjectImpactEqual(self, project, user, expected):
        """ Assert a user's impact on a project. """
        pi = load_project_impact(project, user)
        self.assertEqual(pi.impact, expected)

    def assertProjectImpactExistence(self, project, user, expected):
        """ Assert a existence of a project specific impact in DB. """
        self.assertEqual(Impact.objects.filter(
            user_id=user.id, project_id=project.id).exists(), expected)

    # Helpers

    @staticmethod
    def _mock_complete_solution(impact=100):
        """ Mock a completed solution.

        :param impact: evaluation of impact by contributor
        :return Solution:

        """
        s = mixer.blend('solution.solution')
        s.mark_complete(impact)
        return s

    @staticmethod
    def _mock_valid_solution_vote(solution, is_accepted=True, voter_impact=1):
        """ Mock a valid vote on a solution.

        A valid vote on a solution means the user should also have commented
        on the solution.

        :param solution:
        :param is_accepted:
        :param voter_impact:
        :return Vote:

        """
        v = mixer.blend('joltem.vote', voteable=solution,
                        voter_impact=voter_impact, is_accepted=is_accepted)
        if not is_accepted:
            # needs a comment to count
            mixer.blend('joltem.comment', project=solution.project,
                        owner=v.voter, commentable=solution)
        return v

    # Tests
    # Test chain of signals
    # 1. Vote added to Votable
    # 2. Voteable update project impacts
    # 3. Project impacts update user impacts
    def test_solution_impact(self):
        """ Test impact from a solution. """
        s = self._mock_complete_solution(impact=50)
        self._mock_valid_solution_vote(s, is_accepted=True)
        s = load_model(s)
        self.assertEqual(s.impact, 50)

    def test_project_impact(self):
        """ Test if project specific impact record is being saved in DB. """
        s = self._mock_complete_solution()
        self._mock_valid_solution_vote(s, is_accepted=True)
        self.assertProjectImpactExistence(s.project, s.owner, True)

    def test_project_admin_initial_impact(self):
        """ Test project admin's initial impact.

        A project admin should start out with an impact of 1
        to seed the weighted voting.

        """
        p = mixer.blend('project.project')
        hari = mixer.blend('joltem.user', username='hari')
        # Project impact should not exist as there is no affiliation yet
        self.assertProjectImpactExistence(p, hari, False)
        self.assertImpactEqual(hari, 0)
        # Now lets make Hari an admin
        p.admin_set.add(hari)
        p.save()
        self.assertProjectImpactEqual(p, hari, 1)
        hari = load_model(hari)
        self.assertImpactEqual(hari, 1)

    def test_impact_one_accept(self):
        """ Test impact with a single acceptance vote. """
        s = self._mock_complete_solution(impact=10)
        self._mock_valid_solution_vote(s)
        self.assertEqual(s.get_impact(), 10)
        self.assertEqual(s.get_acceptance(), 100)

    def test_impact_mark_incomplete(self):
        """ Test the effect of marking solution incomplete on impact. """
        s = self._mock_complete_solution(impact=10)
        self._mock_valid_solution_vote(s)
        u = load_model(s.owner)
        self.assertImpactEqual(u, 10)
        self.assertCompletedEqual(u, 1)
        s.mark_incomplete()
        u = load_model(s.owner)
        self.assertImpactEqual(u, 0)
        self.assertCompletedEqual(u, 0)

    def test_rejection_vote_solution(self):
        """ Test rejection vote and the VOTEABLE_THRESHOLD.

        Rejection vote requires comment to count.

        """
        self.assertEqual(VOTEABLE_THRESHOLD, 50)
        s = self._mock_complete_solution(impact=10)
        self._mock_valid_solution_vote(s, is_accepted=True, voter_impact=49)
        s = load_model(s)
        self.assertEqual(s.get_acceptance(), 100)
        self.assertEqual(s.get_impact(), 10)
        self._mock_valid_solution_vote(s, is_accepted=False, voter_impact=51)
        s = load_model(s)
        # using impact instead of get_impact() because want to check DB state
        self.assertEqual(s.get_acceptance(), 49)
        self.assertEqual(s.get_impact(), 0)
