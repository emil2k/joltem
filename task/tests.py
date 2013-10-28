from django.test import TestCase
from django.utils import timezone

from joltem.tests import TestCaseDebugMixin, TEST_LOGGER
from joltem.tests.mocking import *


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

    def test_is_owner(self):
        """
        Test for task is_owner function
        """
        t = get_mock_task(self.project, self.abby, is_reviewed=True, is_accepted=True)
        self.assertFalse(t.is_owner(self.jill))  # admin check
        self.assertFalse(t.is_owner(self.bob))
        self.assertTrue(t.is_owner(self.abby))

    def test_iterate_parents(self):
        """
        Test for iterating through parents of tasks
        """
        s0 = get_mock_solution(self.project, self.abby)
        s1 = get_mock_solution(self.project, self.abby, solution=s0)
        t2 = get_mock_task(self.project, self.abby, solution=s1, is_reviewed=True, is_accepted=True)
        s3 = get_mock_solution(self.project, self.abby, task=t2)
        t4 = get_mock_task(self.project, self.abby, solution=s3, is_reviewed=True, is_accepted=True)

        parents = []
        for parent_solution, parent_task in t4.iterate_parents():
            if parent_solution:
                parents.append(parent_solution)
            else:
                parents.append(parent_task)

        self.assertListEqual(parents, [s3, t2, s1, s0])