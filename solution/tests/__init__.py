""" Solution related tests. """
from django.test import TestCase

from joltem.libs import mixer
from joltem.libs.mock.models import (
    get_mock_user, get_mock_project, get_mock_task, get_mock_solution,
    get_mock_vote, get_mock_comment, get_mock_setup_solution,
    load_project_impact, load_model)
from joltem.models import Vote, Voteable, User
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
        self.project = get_mock_project("hover")
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

    def _mock_complete_solution(self):
        """ Mock a completed solution.

        :return Solution:

        """
        s = mixer.blend('solution.solution')
        s.mark_complete()
        return s

    def _mock_valid_solution_vote(self, solution, magnitude=1, voter_impact=1):
        """ Mock a valid vote on a solution.

        A valid vote on a solution means the user should also have commented
        on the solution.

        :param solution:
        :param magnitude:
        :param voter_impact:
        :return Vote:

        """
        v = mixer.blend('joltem.vote', voteable=solution,
                        voter_impact=voter_impact, magnitude=magnitude,
                        is_accepted=magnitude > 0)
        # needs a comment to count
        mixer.blend('joltem.comment', project=solution.project, owner=v.voter,
                    commentable=solution)
        return v


    # Tests

    # Test chain of signals
    # 1. Vote added to Votable
    # 2. Voteable update project impacts
    # 3. Project impacts update user impacts

    def test_solution_impact(self):
        """ Test impact from a solution. """
        s = self._mock_complete_solution()
        self._mock_valid_solution_vote(s)
        s = load_model(s)
        self.assertTrue(s.impact > 0)

    def test_comment_impact(self):
        """ Test impact from a comment. """
        p = get_mock_project("apple")
        jill = get_mock_user("jill")
        ted = get_mock_user("ted")
        t = get_mock_task(p, jill, is_reviewed=True, is_accepted=True)
        s = get_mock_solution(p, ted, t)
        c = get_mock_comment(p, jill, s)
        get_mock_vote(ted, c, 100, 1)
        c = load_model(c)
        self.assertTrue(c.impact > 0)

    def test_project_impact(self):
        """ Test if project specific impact record is being saved in DB. """
        p = get_mock_project("apple")
        jill = get_mock_user("jill")
        ted = get_mock_user("ted")
        t = get_mock_task(p, jill, is_reviewed=True, is_accepted=True)
        self.assertProjectImpactExistence(p, ted, False)
        s = get_mock_solution(p, ted, t)
        get_mock_vote(jill, s, 100, 1)
        self.assertProjectImpactExistence(p, ted, True)
        # Now test from vote on comment
        self.assertProjectImpactExistence(p, jill, False)
        c = get_mock_comment(p, jill, s)
        get_mock_vote(ted, c, 100, 1)
        self.assertProjectImpactExistence(p, jill, True)

    def test_project_admin_initial_impact(self):
        """ Test project admin's initial impact.

        A project admin should start out with an impact of 1
        to seed the weighted voting.

        """
        p = get_mock_project("terminus")
        hari = get_mock_user("hari")
        # Project impact should not exist as there is no affiliation yet
        self.assertProjectImpactExistence(p, hari, False)
        self.assertImpactEqual(hari, 0)
        # Now if we add a solution, without any votes, the project impact row
        # should be inserted and impact should be 0
        t = get_mock_task(p, hari, is_reviewed=True, is_accepted=True)
        get_mock_solution(p, hari, t)
        self.assertProjectImpactEqual(p, hari, 0)
        self.assertImpactEqual(hari, 0)
        # Now lets make admin
        p.admin_set.add(hari)
        p.save()
        self.assertProjectImpactEqual(p, hari, 1)
        hari = load_model(hari)
        self.assertImpactEqual(hari, 1)

    def test_impact_one_accept(self):
        """ Test impact with a single acceptance vote. """
        s = self._mock_complete_solution()
        self.assertEqual(s.get_impact(), None)
        self.assertEqual(s.get_acceptance(), None)
        self._mock_valid_solution_vote(s)
        self.assertEqual(s.get_impact(), 10)
        self.assertEqual(s.get_acceptance(), 100)

    def test_impact_mark_incomplete(self):
        """ Test the effect of marking solution incomplete on impact. """
        s = self._mock_complete_solution()
        v = self._mock_valid_solution_vote(s, 3, 300)
        u = load_model(s.owner)
        self.assertImpactEqual(u, 10)
        self.assertCompletedEqual(u, 1)
        s.mark_incomplete()
        u = load_model(s.owner)
        self.assertImpactEqual(u, 0)
        self.assertCompletedEqual(u, 0)

    def test_impact_calculation(self):
        """ Test of impact calculations. """

        # Test assumptions
        self.assertEqual(Vote.MAXIMUM_MAGNITUDE, 5,
                         "Maximum magnitude changed.")
        self.assertEqual(Voteable.MAGNITUDE_THRESHOLD, 0.159,
                         "Magnitude threshold changed.")
        self.assertEqual(Impact.SOLUTION_ACCEPTANCE_THRESHOLD, 75,
                         "Solution acceptance threshold changed.")
        self.assertEqual(Impact.COMMENT_ACCEPTANCE_THRESHOLD, 75,
                         "Comment acceptance threshold changed.")

        s = self._mock_complete_solution()

        # Initial
        self.assertListEqual(s.get_impact_distribution(), [0, 0, 0, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals(), [0, 0, 0, 0, 0, 0])

        v = self._mock_valid_solution_vote(s, 2, 100)
        self.assertListEqual(s.get_impact_distribution(), [0, 0, 100, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals(), [
                             100, 100, 100, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v),
                             [0, 0, 0, 0, 0, 0])
        self.assertEqual(s.get_vote_value(v), 10)
        self.assertEqual(s.get_impact(), 10)

        v = self._mock_valid_solution_vote(s, 2, 100)
        self.assertListEqual(s.get_impact_distribution(), [0, 0, 200, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals(), [
                             200, 200, 200, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v),
                             [100, 100, 100, 0, 0, 0])
        self.assertEqual(s.get_vote_value(v), 100)
        self.assertEqual(s.get_impact(), 100)

        v = self._mock_valid_solution_vote(s, 3, 500)
        self.assertListEqual(s.get_impact_distribution(),
                             [0, 0, 200, 500, 0, 0])
        self.assertListEqual(s.get_impact_integrals(),
                             [700, 700, 700, 500, 0, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v),
                             [200, 200, 200, 0, 0, 0])
        self.assertEqual(s.get_vote_value(v), 100)
        self.assertEqual(s.get_impact(), 100)

        v = self._mock_valid_solution_vote(s, 4, 100)
        self.assertListEqual(s.get_impact_distribution(),
                             [0, 0, 200, 500, 100, 0])
        self.assertListEqual(s.get_impact_integrals(),
                             [800, 800, 800, 600, 100, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v),
                             [700, 700, 700, 500, 0, 0])
        self.assertEqual(s.get_vote_value(v), 1000)
        w_sum = 200 * pow(10, 2) + (500 + 100) * pow(10, 3)
        self.assertEqual(s.get_impact(), int(w_sum / float(800)))

        v = self._mock_valid_solution_vote(s, 0, 100)
        self.assertListEqual(s.get_impact_distribution(),
                             [100, 0, 200, 500, 100, 0])
        self.assertListEqual(s.get_impact_integrals(),
                             [900, 800, 800, 600, 100, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v),
                             [800, 800, 800, 600, 100, 0])
        w_sum = 200 * pow(10, 2) + (500 + 100) * pow(10, 3)
        self.assertEqual(s.get_impact(), int(round(w_sum / float(900))))

    def test_rejection_vote_solution(self):
        """ Test rejection vote.

        Rejection vote requires comment to count.

        """
        s = self._mock_complete_solution()
        self.assertEqual(s.impact, None)
        self.assertEqual(s.acceptance, None)
        self._mock_valid_solution_vote(s, 1, 300)
        s = load_model(s)
        self.assertEqual(s.impact, 10)
        self.assertEqual(s.acceptance, 100)
        self._mock_valid_solution_vote(s, 0, 100)
        s = load_model(s)
        # using impact instead of get_impact() because want to check DB state
        self.assertEqual(s.impact, 8)
        self.assertEqual(s.acceptance, 75)

    def test_comment_acceptance_threshold(self):
        """ Test of comment acceptance threshold. """
        self.assertEqual(
            Impact.COMMENT_ACCEPTANCE_THRESHOLD, 75)  # test assumes this value
        p, u, _, s = get_mock_setup_solution("air", "kate")
        bill = get_mock_user("bill")

        self.assertImpactEqual(bill, 0)
        self.assertProjectImpactExistence(p, bill, False)
        c = get_mock_comment(p, bill, s)
        self.assertImpactEqual(bill, 0)  # comment should not affect impact ...
        self.assertProjectImpactExistence(
            p, bill, True)  # .. but it will create this entry
        self.assertEqual(c.acceptance, None)

        get_mock_vote(u, c, 750, 3)
        c = load_model(c)
        self.assertEqual(c.acceptance, 100)
        bill = load_model(bill)
        self.assertImpactEqual(bill, 1)
        self.assertProjectImpactEqual(p, bill, 1)

        # Now rejection votes to lower acceptance
        get_mock_vote(get_mock_user("jade"), c, 100, 0)
        c = load_model(c)
        self.assertEqual(c.acceptance, int(
            round(100 * float(750) / 850)))  # > 75%
        bill = load_model(bill)
        self.assertImpactEqual(bill, 1)
        self.assertProjectImpactEqual(p, bill, 1)

        get_mock_vote(get_mock_user("jill"), c, 150, 0)
        c = load_model(c)
        self.assertEqual(c.acceptance, int(
            round(100 * float(750) / 1000)))  # = 75%
        bill = load_model(bill)
        self.assertImpactEqual(bill, 1)
        self.assertProjectImpactEqual(p, bill, 1)
        get_mock_vote(get_mock_user("gary"), c, 500, 0)
        c = load_model(c)
        self.assertEqual(c.acceptance, int(
            round(100 * float(750) / 1500)))  # < 75%
        bill = load_model(bill)
        self.assertImpactEqual(bill, 0)  # should not count here
        self.assertProjectImpactEqual(p, bill, 0)
