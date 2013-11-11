""" Solution related tests. """

from django.test import TestCase

from joltem.models import Profile, Comment, Vote, Voteable
from project.models import Impact
from solution.models import Solution
from joltem.libs.mocking import (
    get_mock_user, get_mock_project, get_mock_task, get_mock_solution,
    get_mock_vote, get_mock_comment, get_mock_setup_solution,
    load_project_impact, load_model)


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

    # TODO tests that actually test interface using client or selenium
    # TODO tests that check if views follow ownership rules for processing actions


class ImpactTestCase(TestCase):

    """ Test solution impact determination. """

    # Custom assertions

    def assertImpactEqual(self, user, expected):
        """ Assert user's total impact. """
        profile = Profile.objects.get(user_id=user.id)  # don't use get_profile it uses cached results which cause tests to fail
        self.assertEqual(profile.impact, expected)

    def assertCompletedEqual(self, user, expected):
        """ Assert user's completed solutions count. """
        profile = Profile.objects.get(user_id=user.id)  # don't use get_profile it uses cached results which cause tests to fail
        self.assertEqual(profile.completed, expected)

    def assertProjectImpactEqual(self, project, user, expected):
        """ Assert a user's impact on a project. """
        pi = load_project_impact(project, user)
        self.assertEqual(pi.impact, expected)

    def assertProjectImpactExistence(self, project, user, expected):
        """ Assert a existence of a project specific impact in DB. """
        self.assertEqual(Impact.objects.filter(
            user_id=user.id, project_id=project.id).exists(), expected)

    # Tests

    # Test chain of signals
    # 1. Vote added to Votable
    # 2. Voteable update project impacts
    # 3. Project impacts update user impacts

    def test_solution_impact(self):
        """ Test impact from a solution. """
        p = get_mock_project("apple")
        jill = get_mock_user("jill")
        ted = get_mock_user("ted")
        t = get_mock_task(p, jill, is_reviewed=True, is_accepted=True)
        s = get_mock_solution(p, ted, t)
        get_mock_vote(jill, s, 100, 1)
        s = load_model(Solution, s)
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
        c = load_model(Comment, c)
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
        # Now if we add a solution, without any votes, the project impact row should be inserted and impact should be 0
        t = get_mock_task(p, hari, is_reviewed=True, is_accepted=True)
        get_mock_solution(p, hari, t)
        self.assertProjectImpactEqual(p, hari, 0)
        self.assertImpactEqual(hari, 0)
        # Now lets make admin
        p.admin_set.add(hari)
        p.save()
        self.assertProjectImpactEqual(p, hari, 1)
        self.assertImpactEqual(hari, 1)

    def test_impact_one_accept(self):
        """ Test impact with a single acceptance vote. """
        p, bill, t, s = get_mock_setup_solution("lipton", "bill")
        self.assertEqual(s.get_impact(), None)
        self.assertEqual(s.get_acceptance(), None)
        get_mock_vote(get_mock_user("jill"), s, 300, 3)
        self.assertEqual(s.get_impact(), 10)
        self.assertEqual(s.get_acceptance(), 100)

    def test_impact_mark_incomplete(self):
        """ Test the effect of marking solution incomplete on impact. """
        p = get_mock_project("levy")
        jay = get_mock_user("jay")
        t = get_mock_task(p, jay, is_reviewed=True, is_accepted=True)
        self.assertImpactEqual(jay, 0)
        self.assertCompletedEqual(jay, 0)
        s = get_mock_solution(p, jay, t)  # a completed solution added
        self.assertTrue(s.is_completed)
        get_mock_vote(get_mock_user("jill"), s, 300, 3)  # a vote is placed on the solution
        self.assertTrue(s.is_completed)
        self.assertImpactEqual(jay, 10)
        self.assertCompletedEqual(jay, 1)
        # Mark solution incomplete
        s.is_completed = False
        s.time_completed = None
        s.save()
        self.assertFalse(s.is_completed, 0)
        self.assertImpactEqual(jay, 0)
        self.assertCompletedEqual(jay, 0)

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

        p, gary, t, s = get_mock_setup_solution("sonics", "gary")

        # Initial
        self.assertListEqual(s.get_impact_distribution(), [0, 0, 0, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals(), [0, 0, 0, 0, 0, 0])

        v = get_mock_vote(get_mock_user("kate"), s, 100, 2)
        self.assertListEqual(s.get_impact_distribution(), [0, 0, 100, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals(), [100, 100, 100, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v),
                             [0, 0, 0, 0, 0, 0])
        self.assertEqual(s.get_vote_value(v), 10)
        self.assertEqual(s.get_impact(), 10)

        v = get_mock_vote(get_mock_user("janet"), s, 100, 2)
        self.assertListEqual(s.get_impact_distribution(), [0, 0, 200, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals(), [200, 200, 200, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v),
                             [100, 100, 100, 0, 0, 0])
        self.assertEqual(s.get_vote_value(v), 100)
        self.assertEqual(s.get_impact(), 100)

        v = get_mock_vote(get_mock_user("bill"), s, 500, 3)
        self.assertListEqual(s.get_impact_distribution(),
                             [0, 0, 200, 500, 0, 0])
        self.assertListEqual(s.get_impact_integrals(),
                             [700, 700, 700, 500, 0, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v),
                             [200, 200, 200, 0, 0, 0])
        self.assertEqual(s.get_vote_value(v), 100)
        self.assertEqual(s.get_impact(), 100)

        v = get_mock_vote(get_mock_user("susan"), s, 100, 4)
        self.assertListEqual(s.get_impact_distribution(),
                             [0, 0, 200, 500, 100, 0])
        self.assertListEqual(s.get_impact_integrals(),
                             [800, 800, 800, 600, 100, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v),
                             [700, 700, 700, 500, 0, 0])
        self.assertEqual(s.get_vote_value(v), 1000)
        w_sum = 200 * pow(10, 2) + (500 + 100) * pow(10, 3)
        self.assertEqual(s.get_impact(), int(w_sum / float(800)))

        jill = get_mock_user("jill")
        v = get_mock_vote(jill, s, 100, 0)  # rejection vote
        self.assertListEqual(s.get_impact_distribution(),
                             [100, 0, 200, 500, 100, 0])
        self.assertListEqual(s.get_impact_integrals(),
                             [900, 800, 800, 600, 100, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v),
                             [800, 800, 800, 600, 100, 0])
        w_sum = 200 * pow(10, 2) + (500 + 100) * pow(10, 3)
        self.assertEqual(s.get_impact(), int(round(w_sum / float(800))))
        # rejected vote should not count until comment is added
        get_mock_comment(p, jill, s)
        # now should count
        self.assertEqual(s.get_impact(), int(round(w_sum / float(900))))

    def test_rejection_vote_solution(self):
        """ Test rejection vote.

        Rejection vote requires comment to count.

        """
        p, ted, t, s = get_mock_setup_solution("lipton", "ted")
        self.assertEqual(s.impact, None)
        self.assertEqual(s.acceptance, None)
        get_mock_vote(get_mock_user("jill"), s, 300, 1)
        s = load_model(Solution, s)
        self.assertEqual(s.impact, 10)
        self.assertEqual(s.acceptance, 100)
        # Now the rejection vote
        kate = get_mock_user("kate")
        get_mock_vote(kate, s, 100, 0)
        # Vote should not count until commented
        s = load_model(Solution, s)
        self.assertEqual(s.impact, 10)
        self.assertEqual(s.acceptance, 100)
        # Add comment and it should count now
        get_mock_comment(p, kate, s)
        s = load_model(Solution, s)
        self.assertEqual(s.impact, 8)  # using impact instead of get_impact() because want to check DB state
        self.assertEqual(s.acceptance, 75)

    def test_comment_acceptance_threshold(self):
        """ Test of comment acceptance threshold. """
        self.assertEqual(Impact.COMMENT_ACCEPTANCE_THRESHOLD, 75)  # test assumes this value
        p, u, t, s = get_mock_setup_solution("air", "kate")
        bill = get_mock_user("bill")

        self.assertImpactEqual(bill, 0)
        self.assertProjectImpactExistence(p, bill, False)
        c = get_mock_comment(p, bill, s)
        self.assertImpactEqual(bill, 0)  # comment should not affect impact ...
        self.assertProjectImpactExistence(p, bill, True)  # .. but it will create this entry
        self.assertEqual(c.acceptance, None)

        get_mock_vote(u, c, 750, 3)
        c = load_model(Comment, c)
        self.assertEqual(c.acceptance, 100)
        self.assertImpactEqual(bill, 10)
        self.assertProjectImpactEqual(p, bill, 10)

        # Now rejection votes to lower acceptance
        get_mock_vote(get_mock_user("jade"), c, 100, 0)
        c = load_model(Comment, c)
        self.assertEqual(c.acceptance, int(round(100 * float(750) / 850)))  # > 75%
        self.assertImpactEqual(bill, 9)
        self.assertProjectImpactEqual(p, bill, 9)

        get_mock_vote(get_mock_user("jill"), c, 150, 0)
        c = load_model(Comment, c)
        self.assertEqual(c.acceptance, int(round(100 * float(750) / 1000)))  # = 75%
        self.assertImpactEqual(bill, 8)
        self.assertProjectImpactEqual(p, bill, 8)
        get_mock_vote(get_mock_user("gary"), c, 500, 0)
        c = load_model(Comment, c)
        self.assertEqual(c.acceptance, int(round(100 * float(750) / 1500)))  # < 75%
        self.assertImpactEqual(bill, 0)  # should not count here
        self.assertProjectImpactEqual(p, bill, 0)


# Load other tests from submodules
from solution.tests.views import *
