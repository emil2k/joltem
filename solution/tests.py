from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from joltem.models import Profile
from project.models import Project, Impact
from task.models import Task
from solution.models import Solution, Comment, Vote, Voteable

import logging
logger = logging.getLogger('tests')


# Helpers

def get_mock_user(username):
    return User.objects.create_user(username, '%s@gmail.com' % username, '%s_password' % username)


def get_mock_project(name):
    p = Project(
        name=name,
        title="Project : %s" %  name,
    )
    p.save()
    return p


def get_mock_task(project, user, solution=None):
    t = Task(
        title="A task by %s" % user.username,
        owner=user,
        project=project,
        parent=solution
    )
    t.save()
    return t


def get_mock_solution(project, user, task=None, solution=None):
    s = Solution(
        project=project,
        user=user,
        task=task,
        solution=solution
    )
    s.save()
    return s


def get_mock_comment(project, user, solution):
    c = Comment(
        project=project,
        user=user,
        solution=solution
    )
    c.save()
    return c


def get_mock_vote(voter, voteable, voter_impact, magnitude):
    v = Vote(
        voter_impact=voter_impact,  # mock the voter's impact
        is_accepted=magnitude > 0,
        magnitude=magnitude,
        voter=voter,
        voteable=voteable,
    )
    v.save()
    return v


def get_mock_setup_solution(project_name, username):
    """
    A shortcut to get a solution
    """
    p = get_mock_project(project_name)
    u = get_mock_user(username)
    t = get_mock_task(p, u)
    s = get_mock_solution(p, u, t)
    return p, u, t, s


def get_mock_setup_comment(project_name, username):
    """
    A shortcut to get a comment
    """
    p, u, t, s = get_mock_setup_solution(project_name, username)
    c = get_mock_comment(p, u, s)
    return p, u, t, s, c


def load_model(model_class, model_object):
    """
    Load model to check if metrics updated properly
    """
    if model_object:
        return model_class.objects.get(id=model_object.id)


def load_project_impact(project, user):
    """
    Reload votable to check if metrics updated properly
    """
    if project and user:
        return Impact.objects.get(user_id=user.id, project_id=project.id)


def debug_votes(voteable):
    logger.debug("DEBUG VOTES")
    for vote in voteable.vote_set.all():
        logger.debug("VOTE : %s : %d impact : %d mag" % (vote.voter.username, vote.voter_impact, vote.magnitude))


# *********

class TestCaseDebugMixin():

    def setUp(self):
        logger.debug("\n\n///* SETUP : %s\n" % self.id())
        logger.debug("User count %d" % User.objects.all().count() )
        logger.debug("Impact count %d" % Impact.objects.all().count() )

    def tearDown(self):
        logger.debug("\n\n*/// TEARDOWN\n")


class PermissionsTestCase(TestCaseDebugMixin, TestCase):

    def setUp(self):
        super(PermissionsTestCase, self).setUp()
        u = dict()
        self.jill = get_mock_user('jill')  # the project admin
        self.abby = get_mock_user('abby')
        self.bob = get_mock_user('bob')
        self.zack = get_mock_user('zack')
        # Setup project, make Jill admin
        self.project = get_mock_project("hover")
        self.project.admin_set.add(self.jill)
        self.project.save()

    def test_task_is_owner(self):
        """
        Test for task is_owner function
        """
        t = get_mock_task(self.project, self.abby)
        self.assertFalse(t.is_owner(self.jill))  # admin check
        self.assertFalse(t.is_owner(self.bob))
        self.assertTrue(t.is_owner(self.abby))

    def test_solution_is_owner(self):
        """
        Test for solution is_owner function
        """
        t = get_mock_task(self.project, self.bob)
        s = get_mock_solution(self.project, self.zack, t)

        self.assertFalse(s.is_owner(self.jill))
        self.assertFalse(s.is_owner(self.bob))
        self.assertTrue(s.is_owner(self.zack))


    def test_solution_is_acceptor_simple(self):
        """
        Tests for solution is_acceptor owner function,

        When solution has a parent task (not a suggested solution)
        which is not a subtask of a completed or deleted solution.
        """
        t = get_mock_task(self.project, self.bob)
        s = get_mock_solution(self.project, self.abby, t)

        self.assertFalse(s.is_acceptor(self.jill))
        self.assertFalse(s.is_acceptor(self.abby))
        self.assertTrue(s.is_acceptor(self.bob))

    def setup_solution_parents(self):
        """
        Setup a suggested solution hierarchy
        """
        s0 = get_mock_solution(self.project, self.abby)  # root suggested solution
        s1 = get_mock_solution(self.project, self.bob, solution=s0)
        s2 = get_mock_solution(self.project, self.zack, solution=s1)

        self.assertFalse(s2.is_acceptor(self.jill))
        self.assertFalse(s2.is_acceptor(self.abby))
        self.assertTrue(s2.is_acceptor(self.bob))
        self.assertFalse(s2.is_acceptor(self.zack))

        self.assertFalse(s1.is_acceptor(self.jill))
        self.assertTrue(s1.is_acceptor(self.abby))
        self.assertFalse(s1.is_acceptor(self.bob))
        self.assertFalse(s1.is_acceptor(self.zack))

        self.assertTrue(s0.is_acceptor(self.jill))
        self.assertFalse(s0.is_acceptor(self.abby))
        self.assertFalse(s0.is_acceptor(self.bob))
        self.assertFalse(s0.is_acceptor(self.zack))

        return s0, s1, s2

    def test_solution_is_acceptor_parent_completed(self):
        """
        Test of what happens acceptance responsibilities when parents solutions are completed
        """
        s0, s1, s2 = self.setup_solution_parents()

        # Now complete parent solutions

        s1.is_completed = True
        s1.time_completed = timezone.now()
        s1.save()

        self.assertFalse(s2.is_acceptor(self.jill))
        self.assertTrue(s2.is_acceptor(self.abby))
        self.assertFalse(s2.is_acceptor(self.bob))
        self.assertFalse(s2.is_acceptor(self.zack))

        s0.is_completed = True
        s0.time_completed = timezone.now()
        s0.save()

        self.assertTrue(s2.is_acceptor(self.jill))
        self.assertFalse(s2.is_acceptor(self.abby))
        self.assertFalse(s2.is_acceptor(self.bob))
        self.assertFalse(s2.is_acceptor(self.zack))

    def test_solution_is_acceptor_parent_closed(self):
        """
        Test of what happens acceptance responsibilities when parents solutions are closed
        """
        s0, s1, s2 = self.setup_solution_parents()

        # Now delete parent solutions

        s1.is_closed = True
        s1.time_closed = timezone.now()
        s1.save()

        self.assertFalse(s2.is_acceptor(self.jill))
        self.assertTrue(s2.is_acceptor(self.abby))
        self.assertFalse(s2.is_acceptor(self.bob))
        self.assertFalse(s2.is_acceptor(self.zack))

        s0.is_closed = True
        s0.time_closed = timezone.now()
        s0.save()

        self.assertTrue(s2.is_acceptor(self.jill))
        self.assertFalse(s2.is_acceptor(self.abby))
        self.assertFalse(s2.is_acceptor(self.bob))
        self.assertFalse(s2.is_acceptor(self.zack))

    def test_solution_is_acceptor_parent_task_closed(self):
        """
        Test of what happens acceptance responsibilities when parents tasks are closed
        """
        s0, s1, s2 = self.setup_solution_parents()
        jack = get_mock_user("jack")
        gary = get_mock_user("gary")
        t = get_mock_task(self.project, jack, s2)
        s3 = get_mock_solution(self.project, gary, t)

        self.assertFalse(s3.is_acceptor(self.jill))
        self.assertFalse(s3.is_acceptor(self.abby))
        self.assertFalse(s3.is_acceptor(self.bob))
        self.assertFalse(s3.is_acceptor(self.zack))
        self.assertTrue(s3.is_acceptor(jack))
        self.assertFalse(s3.is_acceptor(gary))

        # Now close parent task
        t.is_closed = True
        t.time_closed = timezone.now()
        t.save()

        self.assertFalse(s3.is_acceptor(self.jill))
        self.assertFalse(s3.is_acceptor(self.abby))
        self.assertFalse(s3.is_acceptor(self.bob))
        self.assertTrue(s3.is_acceptor(self.zack))
        self.assertFalse(s3.is_acceptor(jack))
        self.assertFalse(s3.is_acceptor(gary))

        # And complete the parent solution now
        s2.is_completed = True
        s2.time_completed = timezone.now()
        s2.save()

        self.assertFalse(s3.is_acceptor(self.jill))
        self.assertFalse(s3.is_acceptor(self.abby))
        self.assertTrue(s3.is_acceptor(self.bob))
        self.assertFalse(s3.is_acceptor(self.zack))
        self.assertFalse(s3.is_acceptor(jack))
        self.assertFalse(s3.is_acceptor(gary))

    # TODO tests that actually test interface using client or selenium
    # TODO tests that check if views follow ownership rules for processing actions


class ImpactTestCase(TestCaseDebugMixin, TestCase):

    # Custom assertions

    def assertImpactEqual(self, user, expected):
        profile = Profile.objects.get(user_id=user.id)  # don't use get_profile it uses cached results which cause tests to fail
        self.assertEqual(profile.impact, expected)

    def assertProjectImpactEqual(self, project, user, expected):
        pi = load_project_impact(project, user)
        self.assertEqual(pi.impact, expected)

    def assertProjectImpactExistence(self, project, user, expected):
        self.assertEqual(Impact.objects.filter(user_id=user.id, project_id=project.id).exists(), expected)

    # Tests

    # Test chain of signals
    # 1. Vote added to Votable
    # 2. Voteable update project impacts
    # 3. Project impacts update user impacts

    def test_solution_impact(self):
        p = get_mock_project("apple")
        jill = get_mock_user("jill")
        ted = get_mock_user("ted")
        t = get_mock_task(p, jill)
        s = get_mock_solution(p, ted, t)
        get_mock_vote(jill, s, 100, 1)
        s = load_model(Solution, s)
        self.assertTrue(s.impact > 0)

    def test_comment_impact(self):
        p = get_mock_project("apple")
        jill = get_mock_user("jill")
        ted = get_mock_user("ted")
        t = get_mock_task(p, jill)
        s = get_mock_solution(p, ted, t)
        c = get_mock_comment(p, jill, s)
        get_mock_vote(ted, c, 100, 1)
        c = load_model(Comment, c)
        self.assertTrue(c.impact > 0)

    def test_project_impact(self):
        """
        Test if project specific object being created properly
        """
        p = get_mock_project("apple")
        jill = get_mock_user("jill")
        ted = get_mock_user("ted")
        t = get_mock_task(p, jill)
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
        """
        A project admin should start out with an impact of 1 for the specific project to seed the weighted voting
        """
        p = get_mock_project("terminus")
        hari = get_mock_user("hari")
        # Project impact should not exist as there is no affiliation yet
        self.assertProjectImpactExistence(p, hari, False)
        self.assertImpactEqual(hari, 0)
        # Now if we add a solution, without any votes, the project impact row should be inserted and impact should be 0
        t = get_mock_task(p, hari)
        get_mock_solution(p, hari, t)
        self.assertProjectImpactEqual(p, hari, 0)
        self.assertImpactEqual(hari, 0)
        # Now lets make admin
        p.admin_set.add(hari)
        p.save()
        self.assertProjectImpactEqual(p, hari, 1)
        self.assertImpactEqual(hari, 1)

    def test_impact_one_accept(self):
        """
        Test for a lone acceptance vote
        """
        p, bill, t, s = get_mock_setup_solution("lipton", "bill")
        self.assertEqual(s.get_impact(), None)
        self.assertEqual(s.get_acceptance(), None)
        get_mock_vote(get_mock_user("jill"), s, 300, 3)
        logger.info("AFTER JILL VOTE")
        self.assertEqual(s.get_impact(), 10)
        self.assertEqual(s.get_acceptance(), 100)

    def test_impact_calculation(self):
        """
        A test of the impact calculation for a voteable
        """

        # Test assumptions
        self.assertEqual(Vote.MAXIMUM_MAGNITUDE, 5, "Maximum magnitude changed.")
        self.assertEqual(Voteable.MAGNITUDE_THRESHOLD, 0.159, "Magnitude threshold changed.")
        self.assertEqual(Impact.SOLUTION_ACCEPTANCE_THRESHOLD, 75, "Solution acceptance threshold changed.")
        self.assertEqual(Impact.COMMENT_ACCEPTANCE_THRESHOLD, 75, "Comment acceptance threshold changed.")

        p, gary, t, s = get_mock_setup_solution("sonics", "gary")

        # Initial
        self.assertListEqual(s.get_impact_distribution(), [0, 0, 0, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals(), [0, 0, 0, 0, 0, 0])

        v = get_mock_vote(get_mock_user("kate"), s, 100, 2)
        self.assertListEqual(s.get_impact_distribution(), [0, 0, 100, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals(), [100, 100, 100, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v), [0, 0, 0, 0, 0, 0])
        self.assertEqual(s.get_vote_value(v), 10)
        self.assertEqual(s.get_impact(), 10)

        v = get_mock_vote(get_mock_user("janet"), s, 100, 2)
        self.assertListEqual(s.get_impact_distribution(), [0, 0, 200, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals(), [200, 200, 200, 0, 0, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v), [100, 100, 100, 0, 0, 0])
        self.assertEqual(s.get_vote_value(v), 100)
        self.assertEqual(s.get_impact(), 100)

        v = get_mock_vote(get_mock_user("bill"), s, 500, 3)
        self.assertListEqual(s.get_impact_distribution(), [0, 0, 200, 500, 0, 0])
        self.assertListEqual(s.get_impact_integrals(), [700, 700, 700, 500, 0, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v), [200, 200, 200, 0, 0, 0])
        self.assertEqual(s.get_vote_value(v), 100)
        self.assertEqual(s.get_impact(), 100)

        v = get_mock_vote(get_mock_user("susan"), s, 100, 4)
        self.assertListEqual(s.get_impact_distribution(), [0, 0, 200, 500, 100, 0])
        self.assertListEqual(s.get_impact_integrals(), [800, 800, 800, 600, 100, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v), [700, 700, 700, 500, 0, 0])
        self.assertEqual(s.get_vote_value(v), 1000)
        w_sum = 200 * pow(10, 2) + (500 + 100) * pow(10, 3)
        self.assertEqual(s.get_impact(), int(w_sum / float(800)))

        jill = get_mock_user("jill")
        v = get_mock_vote(jill, s, 100, 0)  # rejection vote
        self.assertListEqual(s.get_impact_distribution(), [100, 0, 200, 500, 100, 0])
        self.assertListEqual(s.get_impact_integrals(), [900, 800, 800, 600, 100, 0])
        self.assertListEqual(s.get_impact_integrals_excluding_vote(v), [800, 800, 800, 600, 100, 0])
        w_sum = 200 * pow(10, 2) + (500 + 100) * pow(10, 3)
        self.assertEqual(s.get_impact(), int(round(w_sum / float(800))))
        # rejected vote should not count until comment is added
        get_mock_comment(p, jill, s)
        # now should count
        self.assertEqual(s.get_impact(), int(round(w_sum / float(900))))

    def test_rejection_vote_solution(self):
        """
        Checks that a rejection vote does not count until there is a comment left by that voter in the solution review
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
        """
        Test that comment acceptance threshold works
        """
        self.assertEqual(Impact.COMMENT_ACCEPTANCE_THRESHOLD, 75)  # test assumes this value
        p, u, t, s = get_mock_setup_solution("air","kate")
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
        self.assertEqual(c.acceptance, int(round(100 * float(750)/850)))  # > 75%
        self.assertImpactEqual(bill, 9)
        self.assertProjectImpactEqual(p, bill, 9)

        get_mock_vote(get_mock_user("jill"), c, 150, 0)
        c = load_model(Comment, c)
        self.assertEqual(c.acceptance, int(round(100 * float(750)/1000)))  # = 75%
        self.assertImpactEqual(bill, 8)
        self.assertProjectImpactEqual(p, bill, 8)
        get_mock_vote(get_mock_user("gary"), c, 500, 0)
        c = load_model(Comment, c)
        self.assertEqual(c.acceptance, int(round(100 * float(750)/1500)))  # < 75%
        self.assertImpactEqual(bill, 0)  # should not count here
        self.assertProjectImpactEqual(p, bill, 0)
