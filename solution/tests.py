"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from joltem.models import Profile
from project.models import Project, Impact
from task.models import Task
from solution.models import Solution, Comment, Vote

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


def get_mock_task(project, user):
    t = Task(
        title="A task by %s" % user.username,
        owner=user,
        project=project
    )
    t.save()
    return t


def get_mock_solution(project, user, task):
    s = Solution(
        project=project,
        user=user,
        task=task
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


def load_votable(votable_model, votable):
    """
    Load votable to check if metrics updated properly
    """
    if votable:
        return votable_model.objects.get(id=votable.id)


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

class ImpactTestCase(TestCase):

    def setUp(self):
        logger.debug("\n\n///* SETUP : %s\n" % self.id())
        logger.debug("User count %d" % User.objects.all().count() )
        logger.debug("Impact count %d" % Impact.objects.all().count() )

    def tearDown(self):
        logger.debug("\n\n*/// TEARDOWN\n")

    # Custom assertions

    def assertImpactEqual(self, user, expected):
        profile = Profile.objects.get(user_id=user.id)  # don't use get_profile it uses cached results which cause tests to fail
        self.assertEqual(profile.impact, expected)

    def assertProjectImpactEqual(self, project, user, expected):
        pi = load_project_impact(project, user)
        self.assertEqual(pi.impact, expected)

    def assertProjectImpactExistence(self, project, user, expected):
        self.assertEqual(Impact.objects.filter(user_id=user.id, project_id=project.id).exists(), expected)


class ImpactSignalsTests(ImpactTestCase):

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
        s = load_votable(Solution, s)
        self.assertTrue(s.impact > 0)

    def test_comment_impact(self):
        p = get_mock_project("apple")
        jill = get_mock_user("jill")
        ted = get_mock_user("ted")
        t = get_mock_task(p, jill)
        s = get_mock_solution(p, ted, t)
        c = get_mock_comment(p, jill, s)
        get_mock_vote(ted, c, 100, 1)
        c = load_votable(Comment, c)
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

