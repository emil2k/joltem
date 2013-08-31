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
        t = get_mock_task(self.project, self.abby)
        self.assertFalse(t.is_owner(self.jill))  # admin check
        self.assertFalse(t.is_owner(self.bob))
        self.assertTrue(t.is_owner(self.abby))

    def test_iterate_parents(self):
        """
        Test for iterating through parents of tasks
        """
        s0 = get_mock_solution(self.project, self.abby)
        s1 = get_mock_solution(self.project, self.abby, solution=s0)
        t2 = get_mock_task(self.project, self.abby, solution=s1)
        s3 = get_mock_solution(self.project, self.abby, task=t2)
        t4 = get_mock_task(self.project, self.abby, solution=s3)

        parents = []
        for parent_solution, parent_task in t4.iterate_parents():
            if parent_solution:
                parents.append(parent_solution)
            else:
                parents.append(parent_task)

        self.assertListEqual(parents, [s3, t2, s1, s0])

    def _test_is_acceptor_parent_task(self, is_closed, is_accepted):
        """
        Generates tests for testing is_acceptor parametrized by whether the parent task is closed/accepted
        """
        s0 = get_mock_solution(self.project, self.abby, is_completed=False, is_closed=False)
        t0 = get_mock_task(self.project, self.abby, s0, is_accepted=True, is_closed=False)

        s1 = get_mock_solution(self.project, self.zack, t0, is_completed=False, is_closed=False)
        t1 = get_mock_task(self.project, self.zack, s1, is_accepted=is_accepted, is_closed=is_closed)

        s2 = get_mock_solution(self.project, self.bob, t1, is_completed=False, is_closed=False)
        t2 = get_mock_task(self.project, self.bob, s2, is_accepted=False, is_closed=False)

        # Zack should be the owner either way since if the task is closed
        # he is still the next parent with the solution (s1) being open and incomplete
        self.assertFalse(t2.is_acceptor(self.jill))
        self.assertFalse(t2.is_acceptor(self.bob))
        self.assertFalse(t2.is_acceptor(self.abby))
        self.assertTrue(t2.is_acceptor(self.zack))

        # Now lets mark Zack's solution complete
        s1.is_completed = True
        s1.time_completed = timezone.now()
        s1.save()

        if not is_closed and is_accepted:
            # Zack still acceptor because he is next parent and his task is open and accepted
            self.assertFalse(t2.is_acceptor(self.jill))
            self.assertFalse(t2.is_acceptor(self.bob))
            self.assertFalse(t2.is_acceptor(self.abby))
            self.assertTrue(t2.is_acceptor(self.zack))
        else:
            # Abby should be the acceptor as she is the next parent
            self.assertFalse(t2.is_acceptor(self.jill))
            self.assertFalse(t2.is_acceptor(self.bob))
            self.assertFalse(t2.is_acceptor(self.zack))
            self.assertTrue(t2.is_acceptor(self.abby))

        # Now lets mark Zack's solution incomplete, but closed
        s1.is_completed = False
        s1.time_completed = None
        s1.is_closed = True
        s1.time_closed = timezone.now()
        s1.save()

        if not is_closed and is_accepted:
            # Zack still acceptor because he is next parent and his task is open and accepted
            self.assertFalse(t2.is_acceptor(self.jill))
            self.assertFalse(t2.is_acceptor(self.bob))
            self.assertFalse(t2.is_acceptor(self.abby))
            self.assertTrue(t2.is_acceptor(self.zack))
        else:
            # Abby should be the acceptor as she is the next parent
            self.assertFalse(t2.is_acceptor(self.jill))
            self.assertFalse(t2.is_acceptor(self.bob))
            self.assertFalse(t2.is_acceptor(self.zack))
            self.assertTrue(t2.is_acceptor(self.abby))

    def test_is_acceptor_parent_task_open_accepted(self):
        self._test_is_acceptor_parent_task(False, True)

    def test_is_acceptor_parent_task_closed_accepted(self):
        self._test_is_acceptor_parent_task(True, True)

    def test_is_acceptor_parent_task_open_unaccepted(self):
        self._test_is_acceptor_parent_task(False, False)

    def test_is_acceptor_parent_task_closed_unaccepted(self):
        self._test_is_acceptor_parent_task(True, False)

    def _test_is_acceptor_parent_solution(self, is_closed, is_completed):
        """
        Generates tests for testing is_acceptor parametrized by whether the parent solution is closed/completed
        """
        s0 = get_mock_solution(self.project, self.abby, is_closed=False, is_completed=False)

        # Configure fallback level, if parent solution is unavailable this should become the acceptor
        s0.is_closed = False
        s0.is_completed = False
        s0.save()

        s1 = get_mock_solution(self.project, self.zack, solution=s0, is_closed=is_closed, is_completed=is_completed)

        s2 = get_mock_solution(self.project, self.bob, solution=s1, is_closed=False, is_completed=False)
        t2 = get_mock_task(self.project, self.bob, s2, is_closed=False, is_accepted=False)

        if is_closed or is_completed:  # parent unavailable, should fallback
            self.assertTrue(t2.is_acceptor(self.abby))
            self.assertFalse(t2.is_acceptor(self.zack))
            self.assertFalse(t2.is_acceptor(self.bob))
            self.assertFalse(t2.is_acceptor(self.jill))
        else:  # parent available should be acceptor
            self.assertTrue(t2.is_acceptor(self.zack))
            self.assertFalse(t2.is_acceptor(self.abby))
            self.assertFalse(t2.is_acceptor(self.bob))
            self.assertFalse(t2.is_acceptor(self.jill))

    def test_is_acceptor_parent_solution_open_incomplete(self):
        self._test_is_acceptor_parent_solution(False, False)

    def test_is_acceptor_parent_solution_closed_incomplete(self):
        self._test_is_acceptor_parent_solution(True, False)

    def test_is_acceptor_parent_solution_open_complete(self):
        self._test_is_acceptor_parent_solution(False, True)

    def test_is_acceptor_parent_solution_closed_complete(self):
        self._test_is_acceptor_parent_solution(True, True)

    def test_is_acceptor_root_task(self):
        """
        Test is acceptor for task without a parent solution, meaning a root task,
        a project admin should be an acceptor
        """
        t = get_mock_task(self.project, self.abby, is_accepted=False, is_closed=False)
        self.assertTrue(t.is_acceptor(self.jill))
        self.assertFalse(t.is_acceptor(self.abby))
        self.assertFalse(t.is_acceptor(self.bob))

    def test_is_acceptor_suggested_task(self):
        """
        Test is acceptor for a suggested task, then take away the parent and see if it falls back correctly
        """
        t0 = get_mock_task(self.project, self.abby, is_accepted=True, is_closed=False)

        s1 = get_mock_solution(self.project, self.bob, task=t0, is_completed=False, is_closed=False)
        t1 = get_mock_task(self.project, self.zack, author=self.zack, solution=s1, is_accepted=False, is_closed=False)  # suggested task by zack

        self.assertTrue(t1.is_acceptor(self.bob))
        self.assertFalse(t1.is_acceptor(self.zack))
        self.assertFalse(t1.is_acceptor(self.abby))
        self.assertFalse(t1.is_acceptor(self.jill))

        # Now mark solution complete and abby should become acceptor
        s1.is_completed = True
        s1.time_completed = timezone.now()
        s1.save()

        self.assertTrue(t1.is_acceptor(self.abby))
        self.assertFalse(t1.is_acceptor(self.bob))
        self.assertFalse(t1.is_acceptor(self.zack))
        self.assertFalse(t1.is_acceptor(self.jill))
