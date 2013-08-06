"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from project.models import Project
from solution.models import Solution


class SimpleTest(TestCase):

    fixtures = ['test_users', 'test_tasks']

    def setUp(self):
        self.project = Project.objects.get(id=1)
        self.emil = User.objects.get(id=1)
        self.bob = User.objects.get(id=2)
        self.jill = User.objects.get(id=3)

    def test_fixture(self):
        user = User.objects.get(id=1)
        self.assertEqual(user.username, "emil")

    def test_admin_initial_impact(self):
        project_admins = self.project.admin_set.all()
        self.assertTrue(self.project.admin_set.count() > 0, "Main project has no admins.")
        for project_admin in project_admins:
            self.assertEqual(project_admin.get_profile().impact, 1)  # for the project admin the initial

    def test_solution_no_votes(self):
        task = self.project.task_set.get(id=2)
        solution = Solution(
            project=self.project,
            user=self.bob,
            task=task
        )
        self.assertEqual(solution.impact, None)

