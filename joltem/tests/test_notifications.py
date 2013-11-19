""" Tests for notifications. """

import time

from django.test import TestCase, testcases
from django.contrib.contenttypes.generic import ContentType
from django.core import mail

from ..libs.mix import mixer

from ..libs.mock.models import (get_mock_project, get_mock_task,
                                get_mock_solution, get_mock_user)

from ..models.comments import (NOTIFICATION_TYPE_COMMENT_ADDED,
                               NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL)
from ..models import User
from ..models.votes import (NOTIFICATION_TYPE_VOTE_ADDED,
                            NOTIFICATION_TYPE_VOTE_UPDATED)

from solution.models import (NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE,
                             NOTIFICATION_TYPE_SOLUTION_POSTED)
from task.models import (NOTIFICATION_TYPE_TASK_POSTED,
                         NOTIFICATION_TYPE_TASK_ACCEPTED)


class NotificationTestCase(TestCase):

    """ Test the delivery of notifications, their text and urls. """

    def setUp(self):
        """ Setup notifications test case.

        Create a project and two mock users, jill and bob.

        """
        self.project = get_mock_project("bread", "Sliced Bread")
        self.jill = get_mock_user("jill", first_name="Jill")
        self.bob = get_mock_user("bob", first_name="Bob")

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


class TasksNotificationTestCase(NotificationTestCase):

    """ Test task related notifications. """

    def test_comment_on_task(self):
        """ Test comment notifications delivery from task. """
        task = get_mock_task(self.project, self.jill,
                             is_reviewed=True, is_accepted=True)
        task.add_comment(self.bob, "Bob waz here.")
        self.assertNotificationReceived(
            self.jill, task, NOTIFICATION_TYPE_COMMENT_ADDED,
            "Bob commented on task \"%s\"" % task.title)
        self.assertNotificationNotReceived(
            self.bob, task, NOTIFICATION_TYPE_COMMENT_ADDED,
            "Bob commented on task \"%s\"" % task.title)
        task.add_comment(self.jill, "Ok, Bob.")
        self.assertNotificationReceived(
            self.bob, task, NOTIFICATION_TYPE_COMMENT_ADDED,
            "Jill commented on task \"%s\"" % task.title)
        self.assertNotificationNotReceived(
            self.jill, task, NOTIFICATION_TYPE_COMMENT_ADDED,
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
            self.jill, task, NOTIFICATION_TYPE_COMMENT_ADDED,
            "Bob commented on task \"%s\"" % task.title)

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
        self.assertNotificationNotReceived(self.jill, jill_task,
                                           NOTIFICATION_TYPE_TASK_POSTED)
        self.assertNotificationNotReceived(ted, jill_task,
                                           NOTIFICATION_TYPE_TASK_POSTED)
        self.assertNotificationNotReceived(self.bob, jill_task,
                                           NOTIFICATION_TYPE_TASK_POSTED)

        task = get_mock_task(self.project, self.bob, solution=parent_solution,
                             is_reviewed=True, is_accepted=False)
        self.assertNotificationReceived(
            self.jill, task, NOTIFICATION_TYPE_TASK_POSTED,
            "Bob posted a task on your solution \"%s\"" %
            parent_solution.default_title)
        self.assertNotificationNotReceived(ted, task,
                                           NOTIFICATION_TYPE_TASK_POSTED)
        self.assertNotificationNotReceived(self.bob, task,
                                           NOTIFICATION_TYPE_TASK_POSTED)

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
                                        NOTIFICATION_TYPE_TASK_POSTED,
                                        "Jill posted a task")
        # Don't notify yourself
        self.assertNotificationNotReceived(self.jill, jill_task,
                                           NOTIFICATION_TYPE_TASK_POSTED)
        self.assertNotificationNotReceived(self.bob, jill_task,
                                           NOTIFICATION_TYPE_TASK_POSTED)

        task = get_mock_task(self.project, self.bob,
                             is_reviewed=True, is_accepted=False)
        self.assertNotificationReceived(ted, task,
                                        NOTIFICATION_TYPE_TASK_POSTED,
                                        "Bob posted a task")
        self.assertNotificationReceived(self.jill, task,
                                        NOTIFICATION_TYPE_TASK_POSTED,
                                        "Bob posted a task")
        self.assertNotificationNotReceived(self.bob, task,
                                           NOTIFICATION_TYPE_TASK_POSTED)

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
                                           NOTIFICATION_TYPE_TASK_POSTED)

        # todo Mark it accepted now
        # task.mark_accepted(self.jill)
        # self.assertNotificationReceived(
        #     self.bob, task, NOTIFICATION_TYPE_TASK_ACCEPTED,
        #     "Your task \"%s\" was accepted" % task.title)

    @testcases.skipIf(True, 'disabled')
    def test_task_accepted_suggested(self):
        """ Test notifications when a suggested task is accepted. """
        solution = get_mock_solution(self.project, self.jill,
                                     title="Paint it Blue")
        task = get_mock_task(self.project, self.bob, solution=solution,
                             is_reviewed=True, is_accepted=False)
        self.assertNotificationNotReceived(self.bob, task,
                                           NOTIFICATION_TYPE_TASK_ACCEPTED)
        self.assertNotificationNotReceived(self.jill, task,
                                           NOTIFICATION_TYPE_TASK_ACCEPTED)
        task.mark_accepted(self.jill)
        self.assertNotificationReceived(self.bob, task,
                                        NOTIFICATION_TYPE_TASK_ACCEPTED,
                                        "Your task \"%s\" was accepted" %
                                        task.title)
        self.assertNotificationNotReceived(self.jill, task,
                                           NOTIFICATION_TYPE_TASK_ACCEPTED)
        task.mark_unaccepted()  # should be removed now
        self.assertNotificationNotReceived(self.bob, task,
                                           NOTIFICATION_TYPE_TASK_ACCEPTED)
        self.assertNotificationNotReceived(self.jill, task,
                                           NOTIFICATION_TYPE_TASK_ACCEPTED)


class SolutionNotificationTestCase(NotificationTestCase):

    """ Test notifications related to solutions. """

    def test_solution_complete_for_task(self):
        """ Test notification when a solution for a task is marked complete. """
        task = get_mock_task(self.project, self.jill,
                             is_reviewed=True, is_accepted=True)
        solution = get_mock_solution(self.project, self.bob, task=task)
        solution.mark_complete()
        self.assertNotificationReceived(
            self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE,
            "Solution \"%s\" was marked complete" % solution.default_title)
        # Now mark incomplete and the notification should be gone
        solution.mark_incomplete()
        self.assertNotificationNotReceived(
            self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE)

    def test_solution_complete_for_closed_task(self):
        """ Test notification that solution complete to a closed task owner.

        Since the task is closed there should be no notification.

        """
        task = get_mock_task(self.project, self.jill,
                             is_reviewed=True, is_accepted=True, is_closed=True)
        solution = get_mock_solution(self.project, self.bob, task=task)
        solution.mark_complete()
        self.assertNotificationNotReceived(
            self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE)

    def test_solution_complete_same_owner(self):
        """ Test notification to a task owner.

        Contributed a solution to her own task and marked it complete
        should not receive a notification.

        """
        task = get_mock_task(self.project, self.jill,
                             is_reviewed=True, is_accepted=True)
        solution = get_mock_solution(self.project, self.jill, task=task)
        solution.mark_complete()
        self.assertNotificationNotReceived(
            self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE)

    def test_solution_complete_has_votes(self):
        """ Test notifications on a completed solution.

        A solution that was marked complete more then once, maybe is
        reentering review - all users who previously voted for it
        should be notified and asked to re-review it and revise
        their vote if necessary.

        """
        solution = get_mock_solution(
            self.project, self.bob, title="Making Jam")
        solution.mark_complete()  # solution marked complete for first time
        self.assertNotificationNotReceived(
            self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE)
        solution.put_vote(self.jill, 2)
        solution.mark_incomplete()
        solution.mark_complete()
        self.assertNotificationReceived(
            self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE,
            "Solution \"%s\" was revised, update your vote" %
            solution.default_title)
        solution.mark_incomplete()  # notification should disappear
        self.assertNotificationNotReceived(
            self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE)

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
                                           NOTIFICATION_TYPE_SOLUTION_POSTED)
        solution = get_mock_solution(self.project, self.bob, task=task)
        self.assertNotificationReceived(
            self.jill, solution, NOTIFICATION_TYPE_SOLUTION_POSTED,
            "Bob posted a solution on your task \"%s\"" % task.title)
        self.assertNotificationNotReceived(
            self.bob, solution, NOTIFICATION_TYPE_SOLUTION_POSTED)
        # No notification to the project admin
        self.assertNotificationNotReceived(
            ted, solution, NOTIFICATION_TYPE_SOLUTION_POSTED)

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
                                           NOTIFICATION_TYPE_SOLUTION_POSTED)
        solution = get_mock_solution(self.project, self.bob,
                                     solution=parent_solution)
        self.assertNotificationReceived(
            self.jill, solution, NOTIFICATION_TYPE_SOLUTION_POSTED,
            "Bob posted a solution on your solution \"%s\"" %
            parent_solution.default_title)
        self.assertNotificationNotReceived(
            self.bob, solution, NOTIFICATION_TYPE_SOLUTION_POSTED)
        # No notification to the project admin
        self.assertNotificationNotReceived(
            ted, solution, NOTIFICATION_TYPE_SOLUTION_POSTED)

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
            self.jill, jill_solution, NOTIFICATION_TYPE_SOLUTION_POSTED)
        self.assertNotificationReceived(ted, jill_solution,
                                        NOTIFICATION_TYPE_SOLUTION_POSTED,
                                        "Jill posted a solution")
        solution = get_mock_solution(self.project, self.bob)
        self.assertNotificationReceived(self.jill, solution,
                                        NOTIFICATION_TYPE_SOLUTION_POSTED,
                                        "Bob posted a solution")
        self.assertNotificationReceived(ted, solution,
                                        NOTIFICATION_TYPE_SOLUTION_POSTED,
                                        "Bob posted a solution")
        self.assertNotificationNotReceived(self.bob, solution,
                                           NOTIFICATION_TYPE_SOLUTION_POSTED)

    # Comments on solutions

    def test_comment_on_solution(self):
        """ Test comment notifications delivery from solution. """
        task = get_mock_task(self.project, self.jill, is_reviewed=True,
                             is_accepted=True)
        solution = get_mock_solution(self.project, self.jill, task=task)
        solution.add_comment(self.bob, "Bob waz here.")
        self.assertNotificationReceived(
            self.jill, solution, NOTIFICATION_TYPE_COMMENT_ADDED,
            "Bob commented on solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(
            self.bob, solution, NOTIFICATION_TYPE_COMMENT_ADDED,
            "Bob commented on solution \"%s\"" % solution.default_title)
        solution.add_comment(self.jill, "Ok, Bob.")
        self.assertNotificationReceived(
            self.bob, solution, NOTIFICATION_TYPE_COMMENT_ADDED,
            "Jill commented on solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(
            self.jill, solution, NOTIFICATION_TYPE_COMMENT_ADDED,
            "Jill commented on solution \"%s\"" % solution.default_title)
        # Make sure it is giving you the default title
        solution.title = "MY TITLE"
        solution.save()
        self.assertNotificationReceived(
            self.jill, solution, NOTIFICATION_TYPE_COMMENT_ADDED,
            "Bob commented on solution \"MY TITLE\"")
        self.assertNotificationReceived(
            self.bob, solution, NOTIFICATION_TYPE_COMMENT_ADDED,
            "Jill commented on solution \"MY TITLE\"")

    # Votes on solution

    def test_vote_on_solution(self):
        """ Test notifications for votes on solution. """
        ted = get_mock_user("ted", first_name="Ted")
        solution = get_mock_solution(self.project, self.jill,
                                     title="Cleaning up")
        solution.put_vote(self.bob, 2)
        self.assertNotificationReceived(
            self.jill, solution, NOTIFICATION_TYPE_VOTE_ADDED,
            "Bob voted on your solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(
            self.bob, solution, NOTIFICATION_TYPE_VOTE_ADDED,
            "Bob voted on your solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(
            ted, solution, NOTIFICATION_TYPE_VOTE_ADDED,
            "Bob voted on your solution \"%s\"" % solution.default_title)
        # so that the voting order is established, which effect notification
        # text
        time.sleep(1)
        solution.put_vote(ted, 0)
        # Check that only one notification should just update
        self.assertNotificationReceived(
            self.jill, solution, NOTIFICATION_TYPE_VOTE_ADDED,
            "Ted and Bob voted on your solution \"%s\"" %
            solution.default_title)
        self.assertNotificationNotReceived(
            self.bob, solution, NOTIFICATION_TYPE_VOTE_ADDED,
            "Ted and Bob voted on your solution \"%s\"" %
            solution.default_title)
        self.assertNotificationNotReceived(
            ted, solution, NOTIFICATION_TYPE_VOTE_ADDED,
            "Ted and Bob voted on your solution \"%s\"" %
            solution.default_title)

    def test_vote_updated_on_solution(self):
        """ Test notifications when votes are updated on a solution. """
        solution = get_mock_solution(self.project, self.jill,
                                     title="Cleaning up")
        solution.put_vote(self.bob, 0)
        self.assertNotificationReceived(self.jill, solution,
                                        NOTIFICATION_TYPE_VOTE_ADDED,
                                        "Bob voted on your solution \"%s\"" %
                                        solution.default_title)
        # same vote, check that updated notification is not sent
        solution.put_vote(self.bob, 0)
        self.assertNotificationNotReceived(
            self.jill, solution, NOTIFICATION_TYPE_VOTE_UPDATED,
            "Bob updated a vote on your solution \"%s\"" %
            solution.default_title)
        solution.put_vote(self.bob, 2)
        self.assertNotificationReceived(
            self.jill, solution, NOTIFICATION_TYPE_VOTE_UPDATED,
            "Bob updated a vote on your solution \"%s\"" %
            solution.default_title)
        # check that it creates another notification todo
        solution.put_vote(self.bob, 1)
        self.assertReceivedNotificationCount(
            self.jill, solution, NOTIFICATION_TYPE_VOTE_UPDATED,
            "Bob updated a vote on your solution \"%s\"" %
            solution.default_title, expected_count=2)


class CommentNotificationTestCase(NotificationTestCase):

    """ Test notifications related to comments. """

    def test_vote_on_comment(self):
        """ Test notifications for votes on comments.

        Should only notify when someone marked there comment helpful.

        """
        ted = get_mock_user("ted", first_name="Ted")
        katy = get_mock_user("katy", first_name="Katy")
        solution = get_mock_solution(self.project, self.jill,
                                     title="Cleaning up")
        comment = solution.add_comment(self.bob, "You should add some tests.")
        # negative vote on comment should not trigger notification
        comment.put_vote(ted, 0)
        self.assertNotificationNotReceived(
            self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL)
        comment.put_vote(katy, 2)
        self.assertNotificationReceived(
            self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL,
            "Katy marked your comment helpful")
        time.sleep(1)
        comment.put_vote(self.jill, 1)
        self.assertNotificationReceived(
            self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL,
            "Jill and Katy marked your comment helpful")

    def test_vote_regular_update_on_comment(self):
        """ Test notifications when votes are updated on a comment.

        With out changing is_accepted state.

        """
        solution = get_mock_solution(self.project, self.jill,
                                     title="Cleaning up")
        comment = solution.add_comment(self.bob,
                                       "You should add some tests.")
        comment.put_vote(self.jill, 2)
        self.assertNotificationReceived(
            self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL,
            "Jill marked your comment helpful")
        comment.put_vote(self.jill, 1)
        self.assertNotificationReceived(
            self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL,
            "Jill marked your comment helpful")

    def test_vote_negative_update_on_comment(self):
        """ Test notification when a vote on a comment changes.

        Goes from accepted to unaccepted.

        """
        ted = get_mock_user("ted", first_name="Ted")
        solution = get_mock_solution(self.project, self.jill,
                                     title="Cleaning up")
        comment = solution.add_comment(self.bob, "You should add some tests.")
        comment.put_vote(self.jill, 2)
        self.assertNotificationReceived(
            self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL,
            "Jill marked your comment helpful")
        time.sleep(1)  # to get correct order when sorting by time voted
        comment.put_vote(ted, 1)
        self.assertNotificationReceived(
            self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL,
            "Ted and Jill marked your comment helpful")
        comment.put_vote(self.jill, 0)  # notification still be there
        self.assertNotificationReceived(
            self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL,
            "Ted marked your comment helpful")
        # notification should now be gone as there are no positive votes left
        comment.put_vote(ted, 0)
        self.assertNotificationNotReceived(
            self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL)

    def test_vote_positive_update_on_comment(self):
        """ Test notifications when a vote on a comment changes.

        Goes from unaccepted to accepted

        """
        solution = get_mock_solution(self.project, self.jill,
                                     title="Cleaning up")
        comment = solution.add_comment(self.bob,
                                       "You should add some tests.")
        comment.put_vote(self.jill, 0)
        self.assertNotificationNotReceived(
            self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL)
        # now accepted, should remove notification above
        comment.put_vote(self.jill, 2)
        self.assertNotificationReceived(
            self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL)


class EmailNotificationTestCase(TestCase):

    def setUp(self):
        self.mike = mixer.blend(User)

    def test_disabled(self):
        task = mixer.blend('task.task')
        task.add_comment(self.mike, "Mike waz here.")
        self.assertFalse(mail.outbox)

    def test_immedeately(self):
        task = mixer.blend('task.task',
                           owner__notify_by_email=User.NOTIFY_CHOICES.immediately)
        comment = task.add_comment(self.mike, "Mike are here.")
        self.assertTrue(mail.outbox)

        m = mail.outbox.pop()
        self.assertEqual(m.recipients(), [task.owner.email])
        self.assertEqual(m.subject, '[joltem.com] comment_added')
        self.assertEqual(m.body, '%s commented on task "%s"' % (
            self.mike.first_name,
            task.title
        ))

        task.notify_comment_added(comment)
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
        self.assertEqual(m1.subject, "[joltem.com] Daily diggest")
        self.assertTrue('\n\n' in m1.body)
