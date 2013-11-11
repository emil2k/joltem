from django.test import TestCase

from task.models import Vote
from joltem.tests.mocking import (get_mock_task, get_mock_project,
                                  get_mock_user, get_mock_solution)


class TaskTestCase(TestCase):

    def setUp(self):
        self.project = get_mock_project("zune")
        self.jill = get_mock_user('jill')
        self.jack = get_mock_user('jack')  # other user
        self.task = get_mock_task(self.project, self.jill)

    def test_subtask_count(self):
        self.task.mark_reviewed(self.jill, is_accepted=True)
        s = get_mock_solution(self.project, self.jill, task=self.task)
        t1 = get_mock_task(self.project, self.jack, solution=s,
                           is_reviewed=True, is_accepted=True)
        t2 = get_mock_task(self.project, self.jack, solution=s)  # this one should not count
        self.assertEqual(self.task.get_subtask_count(
            solution_is_closed=False,
            solution_is_completed=False,
            task_is_reviewed=True,
            task_is_accepted=True,
            task_is_closed=False
        ), 1)

    def test_put_vote(self):
        self.task.put_vote(self.jack, True)
        self.assertTrue(Vote.objects.filter(
            voter_id=self.jack.id, task_id=self.task.id,
            is_accepted=True).exists())

    def test_put_vote_overwrite(self):
        self.task.put_vote(self.jack, True)
        self.task.put_vote(self.jack, False)  # overwrite vote
        self.assertTrue(Vote.objects.filter(
            voter_id=self.jack.id, task_id=self.task.id,
            is_accepted=False).exists())

    def test_determine_acceptance(self):
        self.task = get_mock_task(self.project, self.jill)
        self.task.put_vote(self.jack, False)
        self.assertEqual(self.task.vote_set.count(), 1)
        self.assertFalse(self.task.is_accepted)
        self.project.admin_set.add(self.jill)  # make jill an admin of the project
        self.project.save()
        self.task.put_vote(self.jill, True)
        self.assertEqual(self.task.vote_set.count(), 2)
        self.assertTrue(self.task.is_accepted)

    def test_mark_reviewed_accepted(self):
        self.task.mark_reviewed(self.jill, is_accepted=True)
        self.assertTrue(self.task.is_accepted)

    def test_mark_reviewed_rejected(self):
        self.task.mark_reviewed(self.jill, is_accepted=False)
        self.assertFalse(self.task.is_accepted)

    def test_mark_reviewed_accepted_no_parent(self):
        self.assertTrue(self.task.owner_id, self.jill.id)  # assumption, jill owns originally
        self.task.mark_reviewed(self.jack, is_accepted=True)
        self.assertTrue(self.task.owner_id, self.jack.id)  # has no parent solution, so acceptor takes ownership
        self.assertTrue(self.task.is_accepted)

    def test_mark_reviewed_accepted_with_parent(self):
        self.task.mark_reviewed(self.jill, True)
        s = get_mock_solution(self.project, self.jill, task=self.task)
        t = get_mock_task(self.project, self.jack, solution=s)
        t.mark_reviewed(self.jack, is_accepted=True)
        self.assertTrue(t.owner_id, self.jill.id)  # jill is the owner of the parent solution, so it becomes her task
        self.assertTrue(self.task.is_accepted)


class PermissionsTestCase(TestCase):

    def setUp(self):
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
        t = get_mock_task(self.project, self.abby, is_reviewed=True,
                          is_accepted=True)
        self.assertFalse(t.is_owner(self.jill))  # admin check
        self.assertFalse(t.is_owner(self.bob))
        self.assertTrue(t.is_owner(self.abby))

    def test_iterate_parents(self):
        """
        Test for iterating through parents of tasks
        """
        s0 = get_mock_solution(self.project, self.abby)
        s1 = get_mock_solution(self.project, self.abby, solution=s0)
        t2 = get_mock_task(self.project, self.abby, solution=s1,
                           is_reviewed=True, is_accepted=True)
        s3 = get_mock_solution(self.project, self.abby, task=t2)
        t4 = get_mock_task(self.project, self.abby, solution=s3,
                           is_reviewed=True, is_accepted=True)

        parents = []
        for parent_solution, parent_task in t4.iterate_parents():
            if parent_solution:
                parents.append(parent_solution)
            else:
                parents.append(parent_task)

        self.assertListEqual(parents, [s3, t2, s1, s0])
