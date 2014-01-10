""" Tests for notifications. """
import time

from django.contrib.contenttypes.generic import ContentType
from django.core import mail
from django.conf import settings
from django.test import TestCase, testcases

from ..libs.mix import mixer
from ..libs.mock.models import (get_mock_project, get_mock_task,
                                get_mock_solution, get_mock_user)
from ..models import User, Notification


class NotificationTestCase(TestCase):

    """ Test the delivery of notifications, their text and urls. """

    # Custom assertions

    def assertReceivedNotificationCount(
            self, user, notifying, ntype, expected_text=None,
            expected_count=1):
        """ Assert the notification count.

        Keyword arguments :
        user -- receiving the notification.
        notifying -- item that is the target of the notification.
        ntype -- the notification type.
        expected_text -- the expected text of the notification.
        expected_count -- the expected number of notifications expected.

        """
        notifying_type = ContentType.objects.get_for_model(notifying)
        notifications = user.notification_set.filter(
            user_id=user.id,
            notifying_type_id=notifying_type.id,
            notifying_id=notifying.id,
            type=ntype
        )
        match_count = 0
        for notification in notifications:
            actual_text = notifying.get_notification_text(notification)
            if not expected_text:
                match_count += 1
            else:
                if actual_text == expected_text:
                    match_count += 1
        self.assertEqual(expected_count, match_count)

    def assertNotificationReceived(
            self, user, notifying, ntype, expected_text=None):
        """ Assert notification was received by the user.

        Same as assertReceivedNotificationCount() with expected_count = 1.

        """
        self.assertReceivedNotificationCount(user, notifying, ntype,
                                             expected_text, expected_count=1)

    def assertNotificationNotReceived(
            self, user, notifying, ntype, expected_text=None):
        """ Assert notification was not received by the user. """
        self.assertReceivedNotificationCount(user, notifying, ntype,
                                             expected_text, expected_count=0)

    def assertNotificationTextEqual(self, notifying, notification, expected):
        """ Assert notification text equal to expected. """
        actual = notifying.get_notification_text(notification)
        self.assertEqual(
            actual, expected,
            "Notification text not equal to expectation : %s" % actual
        )

    def assertNotificationTextNotEqual(self, notifying, notification, expected):
        """ Assert notification text not equal to expected. """
        self.assertNotEqual(
            notifying.get_notification_text(notification), expected,
            "Notification text equal to value that it shouldn't be.")


class BaseNotificationTestCase(NotificationTestCase):

    """ Contains basic setup for the rest of notification tests. """

    def setUp(self):
        """ Setup notifications test case.

        Create a project and two mock users, jill and bob.

        """
        self.project = get_mock_project("Sliced Bread")
        self.jill = get_mock_user("jill", first_name="Jill")
        self.bob = get_mock_user("bob", first_name="Bob")


class CommonNotificationTestCase(BaseNotificationTestCase):

    def test_mark_cleared(self):
        notifications = mixer.cycle(5).blend(
            'joltem.notification', user=mixer.sequence(self.bob, self.jill),
            owner=self.bob
        )
        n = notifications[0]
        self.assertEqual(
            self.bob.notification_set.filter(is_cleared=False).count(), 3)
        n = n.mark_cleared()
        self.assertEqual(n.is_cleared, True)
        self.assertEqual(
            self.bob.notification_set.filter(is_cleared=False).count(), 2)
        self.bob = type(self.bob).objects.get(pk=self.bob.pk)
        self.assertEqual(self.bob.notifications, 2)

        Notification.objects.filter(user=self.jill).mark_cleared()
        self.assertFalse(self.jill.notification_set.filter(is_cleared=False))
        self.assertTrue(self.bob.notification_set.filter(is_cleared=False))

        Notification.objects.filter(user=self.bob).mark_cleared()
        self.assertFalse(self.bob.notification_set.filter(is_cleared=False))
        self.bob = type(self.bob).objects.get(pk=self.bob.pk)
        self.assertEqual(self.bob.notifications, 0)


class TasksNotificationTestCase(BaseNotificationTestCase):

    """ Test task related notifications. """

    def test_comment_on_task(self):
        """ Test comment notifications delivery from task. """
        task = get_mock_task(self.project, self.jill,
                             is_reviewed=True, is_accepted=True)
        task.add_comment(self.bob, "Bob waz here.")
        self.assertNotificationReceived(
            self.jill, task, settings.NOTIFICATION_TYPES.comment_added,
            "Bob commented on your task \"%s\"" % task.title)
        self.assertNotificationNotReceived(
            self.bob, task, settings.NOTIFICATION_TYPES.comment_added,
            "Bob commented on task \"%s\"" % task.title)
        task.add_comment(self.jill, "Ok, Bob.")
        self.assertNotificationReceived(
            self.bob, task, settings.NOTIFICATION_TYPES.comment_added,
            "Jill commented on task \"%s\"" % task.title)
        self.assertNotificationNotReceived(
            self.jill, task, settings.NOTIFICATION_TYPES.comment_added,
            "Jill commented on task \"%s\"" % task.title)

    def test_multiple_comments_on_task(self):
        """ Test multiple comments by one user.

        Notifications should update instead of creating new notifications.

        """
        task = get_mock_task(self.project, self.jill,
                             is_reviewed=True, is_accepted=True)
        task.add_comment(self.bob, "Bob waz here.")
        task.add_comment(self.jill, "Bob waz here.")
        task.add_comment(self.bob, "Bob waz here.")
        # Jill should only have one notification from Bob
        self.assertNotificationReceived(
            self.jill, task, settings.NOTIFICATION_TYPES.comment_added,
            "Bob commented on your task \"%s\"" % task.title)

    def test_task_posted_with_parent(self):
        """ Test notifications when task is posted with a parent solution.

        Notify solution owner, if it is not same person who posted the task.

        """
        ted = get_mock_user("ted", first_name="Ted")  # project admin
        self.project.admin_set.add(ted)
        self.project.save()

        parent_solution = get_mock_solution(self.project, self.jill,
                                            title="Wood Floor")
        jill_task = get_mock_task(self.project, self.jill,
                                  solution=parent_solution,
                                  is_reviewed=True, is_accepted=False)
        # Don't notify yourself
        self.assertNotificationNotReceived(
            self.jill, jill_task, settings.NOTIFICATION_TYPES.task_posted)
        self.assertNotificationNotReceived(
            ted, jill_task, settings.NOTIFICATION_TYPES.task_posted)
        self.assertNotificationNotReceived(self.bob, jill_task,
                                           settings.NOTIFICATION_TYPES.task_posted)

        task = get_mock_task(self.project, self.bob, solution=parent_solution,
                             is_reviewed=True, is_accepted=False)
        self.assertNotificationReceived(
            self.jill, task, settings.NOTIFICATION_TYPES.task_posted,
            "Bob posted a task on your solution \"%s\"" %
            parent_solution.default_title)
        self.assertNotificationNotReceived(ted, task,
                                           settings.NOTIFICATION_TYPES.task_posted)
        self.assertNotificationNotReceived(self.bob, task,
                                           settings.NOTIFICATION_TYPES.task_posted)

    def test_task_posted_no_parent(self):
        """ Test notifications when task is posted without parents.

        Notify project admins, excluding the person who posted the task.

        """
        self.project.admin_set.add(self.jill)
        # test with multiple project admins
        ted = get_mock_user("ted", first_name="Ted")
        self.project.admin_set.add(ted)
        self.project.save()

        jill_task = get_mock_task(self.project, self.jill,
                                  is_reviewed=True, is_accepted=False)
        self.assertNotificationReceived(ted, jill_task,
                                        settings.NOTIFICATION_TYPES.task_posted,
                                        "Jill posted a task")
        # Don't notify yourself
        self.assertNotificationNotReceived(self.jill, jill_task,
                                           settings.NOTIFICATION_TYPES.task_posted)
        self.assertNotificationNotReceived(self.bob, jill_task,
                                           settings.NOTIFICATION_TYPES.task_posted)

        task = get_mock_task(self.project, self.bob,
                             is_reviewed=True, is_accepted=False)
        self.assertNotificationReceived(ted, task,
                                        settings.NOTIFICATION_TYPES.task_posted,
                                        "Bob posted a task")
        self.assertNotificationReceived(self.jill, task,
                                        settings.NOTIFICATION_TYPES.task_posted,
                                        "Bob posted a task")
        self.assertNotificationNotReceived(self.bob, task,
                                           settings.NOTIFICATION_TYPES.task_posted)

    def test_task_accepted(self):
        """ Test notifications when a regular task.

        Created by the owner of a solution, is a solution.

        """
        get_mock_solution(self.project, self.jill, title="Paint it Red")
        parent_task = get_mock_task(self.project, self.jill,
                                    is_reviewed=True, is_accepted=True)

        solution = get_mock_solution(self.project, self.bob, task=parent_task)
        task = get_mock_task(self.project, self.bob, solution=solution,
                             is_reviewed=True, is_accepted=False)
        self.assertNotificationNotReceived(self.bob, task,
                                           settings.NOTIFICATION_TYPES.task_posted)

        # todo Mark it accepted now
        # task.mark_accepted(self.jill)
        # self.assertNotificationReceived(
        #     self.bob, task, settings.NOTIFICATION_TYPES.task_accepted,
        #     "Your task \"%s\" was accepted" % task.title)

    @testcases.skipIf(True, 'disabled')
    def test_task_accepted_suggested(self):
        """ Test notifications when a suggested task is accepted. """
        solution = get_mock_solution(self.project, self.jill,
                                     title="Paint it Blue")
        task = get_mock_task(self.project, self.bob, solution=solution,
                             is_reviewed=True, is_accepted=False)
        self.assertNotificationNotReceived(self.bob, task,
                                           settings.NOTIFICATION_TYPES.task_accepted)
        self.assertNotificationNotReceived(self.jill, task,
                                           settings.NOTIFICATION_TYPES.task_accepted)
        task.mark_accepted(self.jill)
        self.assertNotificationReceived(self.bob, task,
                                        settings.NOTIFICATION_TYPES.task_accepted,
                                        "Your task \"%s\" was accepted" %
                                        task.title)
        self.assertNotificationNotReceived(self.jill, task,
                                           settings.NOTIFICATION_TYPES.task_accepted)
        task.mark_unaccepted()  # should be removed now
        self.assertNotificationNotReceived(self.bob, task,
                                           settings.NOTIFICATION_TYPES.task_accepted)
        self.assertNotificationNotReceived(self.jill, task,
                                           settings.NOTIFICATION_TYPES.task_accepted)


class SolutionNotificationTestCase(BaseNotificationTestCase):

    """ Test notifications related to solutions. """

    def test_solution_complete_for_task(self):
        """ Test notification when a solution for a task is marked complete. """
        task = get_mock_task(self.project, self.jill,
                             is_reviewed=True, is_accepted=True)
        solution = get_mock_solution(self.project, self.bob, task=task)
        solution.mark_complete(5)
        self.assertNotificationReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.solution_marked_complete,
            "Solution \"%s\" was marked complete" % solution.default_title)
        # Now mark incomplete and the notification should be gone
        solution.mark_incomplete()
        self.assertNotificationNotReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.solution_marked_complete)

    def test_solution_complete_for_closed_task(self):
        """ Test notification that solution complete to a closed task owner.

        Since the task is closed there should be no notification.

        """
        task = get_mock_task(self.project, self.jill,
                             is_reviewed=True, is_accepted=True, is_closed=True)
        solution = get_mock_solution(self.project, self.bob, task=task)
        solution.mark_complete(5)
        self.assertNotificationNotReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.solution_marked_complete)

    def test_solution_complete_same_owner(self):
        """ Test notification to a task owner.

        Contributed a solution to her own task and marked it complete
        should not receive a notification.

        """
        task = get_mock_task(self.project, self.jill,
                             is_reviewed=True, is_accepted=True)
        solution = get_mock_solution(self.project, self.jill, task=task)
        solution.mark_complete(5)
        self.assertNotificationNotReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.solution_marked_complete)

    def test_solution_posted_with_parent_task(self):
        """ Test notifications that a solution has been posted.

        If the solution has a parent task, notify parent task owner.

        """
        ted = get_mock_user("ted", first_name="Ted")  # project admin
        self.project.admin_set.add(ted)
        self.project.save()

        task = get_mock_task(self.project, self.jill,
                             is_reviewed=True, is_accepted=True)
        jill_solution = get_mock_solution(self.project, self.jill, task=task)
        # Don't notify yourself
        self.assertNotificationNotReceived(self.jill, jill_solution,
                                           settings.NOTIFICATION_TYPES.solution_posted)
        solution = get_mock_solution(self.project, self.bob, task=task)
        self.assertNotificationReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.solution_posted,
            "Bob posted a solution on your task \"%s\"" % task.title)
        self.assertNotificationNotReceived(
            self.bob, solution, settings.NOTIFICATION_TYPES.solution_posted)
        # No notification to the project admin
        self.assertNotificationNotReceived(
            ted, solution, settings.NOTIFICATION_TYPES.solution_posted)

    def test_solution_posted_with_parent_solution(self):
        """ Test notifications that a solution has been posted.

        If the solution has a parent solution, notify parent solution owner.

        """
        ted = get_mock_user("ted", first_name="Ted")  # project admin
        self.project.admin_set.add(ted)
        self.project.save()

        parent_solution = get_mock_solution(self.project, self.jill,
                                            title="Doodle")
        jill_solution = get_mock_solution(self.project, self.jill,
                                          solution=parent_solution)
        # Don't notify yourself
        self.assertNotificationNotReceived(self.jill, jill_solution,
                                           settings.NOTIFICATION_TYPES.solution_posted)
        solution = get_mock_solution(self.project, self.bob,
                                     solution=parent_solution)
        self.assertNotificationReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.solution_posted,
            "Bob posted a solution on your solution \"%s\"" %
            parent_solution.default_title)
        self.assertNotificationNotReceived(
            self.bob, solution, settings.NOTIFICATION_TYPES.solution_posted)
        # No notification to the project admin
        self.assertNotificationNotReceived(
            ted, solution, settings.NOTIFICATION_TYPES.solution_posted)

    def test_solution_posted_no_parent(self):
        """ Test notifications that a solution has been posted.

        If the solution has no parents, notify the project administrators.

        """
        self.project.admin_set.add(self.jill)
        # test with multiple project admins
        ted = get_mock_user("ted", first_name="Ted")
        self.project.admin_set.add(ted)
        self.project.save()

        jill_solution = get_mock_solution(self.project, self.jill)
        # Don't notify yourself
        self.assertNotificationNotReceived(
            self.jill, jill_solution, settings.NOTIFICATION_TYPES.solution_posted)
        self.assertNotificationReceived(ted, jill_solution,
                                        settings.NOTIFICATION_TYPES.solution_posted,
                                        "Jill posted a solution")
        solution = get_mock_solution(self.project, self.bob)
        self.assertNotificationReceived(self.jill, solution,
                                        settings.NOTIFICATION_TYPES.solution_posted,
                                        "Bob posted a solution")
        self.assertNotificationReceived(ted, solution,
                                        settings.NOTIFICATION_TYPES.solution_posted,
                                        "Bob posted a solution")
        self.assertNotificationNotReceived(self.bob, solution,
                                           settings.NOTIFICATION_TYPES.solution_posted)

    # Comments on solutions

    def test_comment_on_solution(self):
        """ Test comment notifications delivery from solution. """
        task = get_mock_task(self.project, self.jill, is_reviewed=True,
                             is_accepted=True)
        solution = get_mock_solution(self.project, self.jill, task=task)
        solution.add_comment(self.bob, "Bob waz here.")
        self.assertNotificationReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.comment_added,
            "Bob commented on solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(
            self.bob, solution, settings.NOTIFICATION_TYPES.comment_added,
            "Bob commented on solution \"%s\"" % solution.default_title)
        solution.add_comment(self.jill, "Ok, Bob.")
        self.assertNotificationReceived(
            self.bob, solution, settings.NOTIFICATION_TYPES.comment_added,
            "Jill commented on solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.comment_added,
            "Jill commented on solution \"%s\"" % solution.default_title)
        # Make sure it is giving you the default title
        solution.title = "MY TITLE"
        solution.save()
        self.assertNotificationReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.comment_added,
            "Bob commented on solution \"MY TITLE\"")
        self.assertNotificationReceived(
            self.bob, solution, settings.NOTIFICATION_TYPES.comment_added,
            "Jill commented on solution \"MY TITLE\"")

    # Votes on solution

    def test_vote_on_solution(self):
        """ Test notifications for votes on solution. """
        ted = get_mock_user("ted", first_name="Ted")
        solution = get_mock_solution(self.project, self.jill,
                                     title="Cleaning up")
        solution.put_vote(self.bob, 2)
        self.assertNotificationReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.vote_added,
            "Bob voted on your solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(
            self.bob, solution, settings.NOTIFICATION_TYPES.vote_added,
            "Bob voted on your solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(
            ted, solution, settings.NOTIFICATION_TYPES.vote_added,
            "Bob voted on your solution \"%s\"" % solution.default_title)
        # so that the voting order is established, which effect notification
        # text
        time.sleep(1)
        solution.put_vote(ted, 0)
        # Check that only one notification should just update
        self.assertNotificationReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.vote_added,
            "Ted and Bob voted on your solution \"%s\"" %
            solution.default_title)
        self.assertNotificationNotReceived(
            self.bob, solution, settings.NOTIFICATION_TYPES.vote_added,
            "Ted and Bob voted on your solution \"%s\"" %
            solution.default_title)
        self.assertNotificationNotReceived(
            ted, solution, settings.NOTIFICATION_TYPES.vote_added,
            "Ted and Bob voted on your solution \"%s\"" %
            solution.default_title)

    def test_vote_updated_on_solution(self):
        """ Test notifications when votes are updated on a solution. """
        solution = get_mock_solution(self.project, self.jill,
                                     title="Cleaning up")
        solution.put_vote(self.bob, False)
        self.assertNotificationReceived(self.jill, solution,
                                        settings.NOTIFICATION_TYPES.vote_added,
                                        "Bob voted on your solution \"%s\"" %
                                        solution.default_title)
        # same vote, check that updated notification is not sent
        solution.put_vote(self.bob, False)
        self.assertNotificationNotReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.vote_updated,
            "Bob updated a vote on your solution \"%s\"" %
            solution.default_title)
        solution.put_vote(self.bob, True)
        self.assertNotificationReceived(
            self.jill, solution, settings.NOTIFICATION_TYPES.vote_updated,
            "Bob updated a vote on your solution \"%s\"" %
            solution.default_title)
        # check that it creates another notification instead of replacing
        solution.put_vote(self.bob, False)
        self.assertReceivedNotificationCount(
            self.jill, solution, settings.NOTIFICATION_TYPES.vote_updated,
            "Bob updated a vote on your solution \"%s\"" %
            solution.default_title, expected_count=2)

    def test_solution_evaluation_changed(self):
        """ Test notification when solution evaluation changes.

        Notification is sent to all the voters, informing them to update
        their vote as the vote is cleared when this happens.

        Also test that new notifications are created each time, instead
        of updating.

        """
        solution = mixer.blend('solution.solution', title="Bird House")
        solution.mark_complete(5)
        voter = mixer.blend('joltem.user')
        solution.put_vote(voter, True)
        solution.change_evaluation(10)
        self.assertNotificationReceived(
            voter, solution, settings.NOTIFICATION_TYPES.solution_evaluation_changed,
            'Update your vote, the evaluation of "Bird House" was changed')
        solution.put_vote(voter, True)
        solution.change_evaluation(5)  # should create new notification
        self.assertReceivedNotificationCount(
            voter, solution, settings.NOTIFICATION_TYPES.solution_evaluation_changed,
            'Update your vote, the evaluation of "Bird House" was changed',
            expected_count=2)


class EmailNotificationTestCase(TestCase):

    def setUp(self):
        self.mike = mixer.blend(User)

    def test_disabled(self):
        task = mixer.blend('task.task')
        task.add_comment(self.mike, "Mike waz here.")
        self.assertFalse(mail.outbox)

    def test_immedeately(self):
        task = mixer.blend(
            'task.task', owner__notify_by_email=User.NOTIFY_CHOICES.immediately)
        comment = task.add_comment(self.mike, "Mike are here.")
        self.assertTrue(mail.outbox)

        m = mail.outbox.pop()
        self.assertEqual(m.recipients(), [task.owner.email])
        self.assertEqual(m.subject, '[joltem.com] comment_added')

        self.assertTrue('%s commented on your task "%s"' % (
            self.mike.first_name,
            task.title
        ) in m.body)

        task.notify_comment_added(comment)
        self.assertFalse(mail.outbox)

        [notification] = task.owner.notification_set.all()
        notification.save()
        self.assertFalse(mail.outbox)

    def test_diggest(self):
        task1 = mixer.blend(
            'task.task', owner__notify_by_email=User.NOTIFY_CHOICES.daily)

        task2 = mixer.blend(
            'task.task', owner__notify_by_email=User.NOTIFY_CHOICES.daily)

        task1.add_comment(self.mike, "Comment")
        task1.add_comment(task2.owner, "Comment")
        task1.add_comment(task2.author, "Comment")
        task2.add_comment(self.mike, "Comment")
        task2.add_comment(task1.owner, "Comment")
        task2.add_comment(task1.author, "Comment")

        self.assertFalse(mail.outbox)

        from joltem.tasks import daily_diggest
        daily_diggest.delay()

        self.assertEqual(len(mail.outbox), 2)

        m1 = mail.outbox.pop()
        m2 = mail.outbox.pop()
        self.assertNotEqual(m1.to, m2.to)
        self.assertTrue("Joltem" in m1.body)
        self.assertEqual(m1.subject, "[joltem.com] Daily diggest")
        self.assertTrue('\n\n' in m1.body)
