"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core import management
from project.models import Project
from solution.models import Solution, Vote

import logging
logger = logging.getLogger('tests')


def setup():
    management.call_command('loaddata', 'test_users.json', verbosity=0)
    management.call_command('loaddata', 'test_tasks.json', verbosity=0)


def teardown():
    management.call_command('flush', verbosity=0, interactive=False)


class SimpleTest(TestCase):

    def setUp(self):
        self.project = Project.objects.get(id=1)
        self.emil = User.objects.get(id=1)
        self.bob = User.objects.get(id=2)
        self.jill = User.objects.get(id=3)

    def get_mock_vote(self, voter, voteable, voter_impact, magnitude):
        return Vote(
            voter_impact=voter_impact,  # mock the voter's impact
            is_accepted=magnitude > 0,
            magnitude=magnitude,
            voter=voter,
            voteable=voteable,
        )

    def test_fixture(self):
        user = User.objects.get(id=1)
        self.assertEqual(user.username, "emil")

    def test_admin_initial_impact(self):
        project_admins = self.project.admin_set.all()
        self.assertTrue(self.project.admin_set.count() > 0, "Main project has no admins.")
        for project_admin in project_admins:
            self.assertEqual(project_admin.get_profile().impact, 1)  # for the project admin the initial

    def test_solution_votes(self):
        task = self.project.task_set.get(id=2)
        solution = Solution(
            project=self.project,
            user=self.bob,
            task=task
        )
        solution.save()
        # No votes, should be none
        self.assertEqual(solution.impact, None)
        # Add a vote from someone who has no impact
        self.get_mock_vote(self.emil, solution, 0, 1).save()
        for vote in solution.vote_set.all():
            logger.debug("VOTE : %s : %d impact : %d mag" % (vote.voter.username, vote.voter_impact, vote.magnitude))
        self.assertEqual(solution.impact, None)
        # Add a check vote
        self.get_mock_vote(self.emil, solution, 500, 1).save()
        self.assertEqual(solution.impact, 10)
        # Add a exceptional vote
        self.get_mock_vote(self.jill, solution, 100, 2).save()
        self.assertEqual(solution.impact, 10)
        for vote in solution.vote_set.all():
            logger.debug("VOTE : %s : %d impact : %d mag" % (vote.voter.username, vote.voter_impact, vote.magnitude))


