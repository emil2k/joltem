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


def setup():
    management.call_command('loaddata', 'test_users', verbosity=0)
    management.call_command('loaddata', 'test_task.json', verbosity=0)


def teardown():
    management.call_command('flush', verbosity=0, interactive=False)


class SolutionTestCase(TestCase):

    def setUp(self):
        self.project = Project.objects.get(id=1)
        self.emil = User.objects.get(id=1)
        self.bob = User.objects.get(id=2)
        self.jill = User.objects.get(id=3)
        self.kate = User.objects.get(id=4)
        self.task = Task.objects.get(id=1)
        self.solution = Solution(
            project=self.project,
            user=self.bob,
            task=self.task
        )
        self.solution.save()

    def debug_votes(self):
        logger.debug("DEBUG VOTES")
        for vote in self.solution.vote_set.all():
            logger.debug("VOTE : %s : %d impact : %d mag" % (vote.voter.username, vote.voter_impact, vote.magnitude))


    @classmethod
    def get_mock_vote(cls, voter, voteable, voter_impact, magnitude):
        return Vote(
            voter_impact=voter_impact,  # mock the voter's impact
            is_accepted=magnitude > 0,
            magnitude=magnitude,
            voter=voter,
            voteable=voteable,
        )

    @classmethod
    def reload_votable(cls, votable_model, votable):
        """
        Reload votable to check if metrics updated properly
        """
        if votable:
            return votable_model.objects.get(id=votable.id)

    # Test chain of signals
    # 1. Vote added to Votable
    # 2. Voteable update project impacts
    # 3. Project impacts update user impacts

    def test_solution_impact(self):
        s = Solution(
            project=self.project,
            user=self.bob,
            task=self.task
        )
        s.save()
        SolutionTestCase.get_mock_vote(self.emil, s, 100, 1).save()
        s = SolutionTestCase.reload_votable(Solution, s)
        self.assertTrue(s.impact > 0)

    def test_comment_impact(self):
        c = Comment(
            project=self.project,
            user=self.bob,
            solution_id=1
        )
        c.save()
        SolutionTestCase.get_mock_vote(self.emil, c, 100, 1).save()
        c = SolutionTestCase.reload_votable(Comment, c)
        self.assertTrue(c.impact > 0)

    def test_project_impact(self):
        # Project impact from solution
        self.assertFalse(Impact.objects.filter(user_id=self.kate.id, project_id=self.project.id).exists())
        s = Solution(
            project=self.project,
            user=self.kate,
            task=self.task
        )
        s.save()
        SolutionTestCase.get_mock_vote(self.emil, s, 100, 1).save()
        self.assertTrue(Impact.objects.filter(user_id=self.kate.id, project_id=self.project.id).exists())
        # Now leave a comment
        self.assertFalse(Impact.objects.filter(user_id=self.jill.id, project_id=self.project.id).exists())
        c = Comment(
            project=self.project,
            user=self.jill,
            solution=s
        )
        c.save()
        SolutionTestCase.get_mock_vote(self.emil, c, 100, 1).save()
        self.assertTrue(Impact.objects.filter(user_id=self.jill.id, project_id=self.project.id).exists())


    # TODO test admin initial impact


