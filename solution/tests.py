"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core import management
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


def reload_votable(votable_model, votable):
    """
    Reload votable to check if metrics updated properly
    """
    if votable:
        return votable_model.objects.get(id=votable.id)


def debug_votes(voteable):
    logger.debug("DEBUG VOTES")
    for vote in voteable.vote_set.all():
        logger.debug("VOTE : %s : %d impact : %d mag" % (vote.voter.username, vote.voter_impact, vote.magnitude))


class ImpactSignalsTests(TestCase):

    def setUp(self):
        logger.debug("\n\n///* SETUP : %s\n" % self.id())
        logger.debug("User count %d" % User.objects.all().count() )
        logger.debug("Impact count %d" % Impact.objects.all().count() )

    def tearDown(self):
        logger.debug("\n\n*/// TEARDOWN\n")

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
        s = reload_votable(Solution, s)
        self.assertTrue(s.impact > 0)

    def test_comment_impact(self):
        p = get_mock_project("apple")
        jill = get_mock_user("jill")
        ted = get_mock_user("ted")
        t = get_mock_task(p, jill)
        s = get_mock_solution(p, ted, t)
        c = get_mock_comment(p, jill, s)
        get_mock_vote(ted, c, 100, 1)
        c = reload_votable(Comment, c)
        self.assertTrue(c.impact > 0)

    def test_project_impact(self):
        """
        Test if project specific object being created properly
        """
        p = get_mock_project("apple")
        jill = get_mock_user("jill")
        ted = get_mock_user("ted")
        t = get_mock_task(p, jill)
        self.assertFalse(Impact.objects.filter(user_id=ted.id, project_id=p.id).exists())
        s = get_mock_solution(p, ted, t)
        get_mock_vote(jill, s, 100, 1)
        self.assertTrue(Impact.objects.filter(user_id=ted.id, project_id=p.id).exists())
        # Now test from vote on comment
        self.assertFalse(Impact.objects.filter(user_id=jill.id, project_id=p.id).exists())
        c = get_mock_comment(p, jill, s)
        get_mock_vote(ted, c, 100, 1)
        self.assertTrue(Impact.objects.filter(user_id=jill.id, project_id=p.id).exists())


    # TODO test admin initial impact


