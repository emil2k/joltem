from django.test import TestCase
from django.contrib.contenttypes.generic import ContentType

from joltem.tests import TestCaseDebugMixin, TEST_LOGGER
from joltem.tests.mocking import *

from joltem.models.comments import NOTIFICATION_TYPE_COMMENT_ADDED, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL
from joltem.models.votes import NOTIFICATION_TYPE_VOTE_ADDED, NOTIFICATION_TYPE_VOTE_UPDATED
from solution.models import NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE, NOTIFICATION_TYPE_SOLUTION_POSTED
from task.models import NOTIFICATION_TYPE_TASK_POSTED, NOTIFICATION_TYPE_TASK_ACCEPTED

import time


class NotificationTestCase(TestCaseDebugMixin, TestCase):
    """
    Test case to test the delivery of notifications, and their text and urls
    """

    def setUp(self):
        super(NotificationTestCase, self).setUp()
        self.project = get_mock_project("bread", "Sliced Bread")
        self.jill = get_mock_user("jill", first_name="Jill")
        self.bob = get_mock_user("bob", first_name="Bob")

    # Custom assertions

    def assertReceivedNotificationCount(self, user, notifying, type, expected_text=None, expected_count=1):
        """
        Check the notification count
        If `count` is specified it should be exactly that many
        """
        TEST_LOGGER.debug("ASSERT RECEIVED NOTIFICATION : %s" % user)
        notifying_type = ContentType.objects.get_for_model(notifying)
        notifications = user.notification_set.filter(
            user_id=user.id,
            notifying_type_id=notifying_type.id,
            notifying_id=notifying.id,
            type=type
        )
        match_count = 0
        for notification in notifications:
            actual_text = notifying.get_notification_text(notification)
            TEST_LOGGER.debug("NOTIFICATION TEXT : %s" % actual_text)
            if not expected_text:
                match_count += 1
            else:
                if actual_text == expected_text:
                    match_count += 1
        self.assertEqual(expected_count, match_count)

    def assertNotificationReceived(self, user, notifying, type, expected_text=None):
        """
        Checks if a notification was received by the user, from the notifying instance
        if expected text is passed checks that the text matches also

        Assumes only one notification meets parameters, otherwise fails
        """
        self.assertReceivedNotificationCount(user, notifying, type, expected_text, expected_count=1)

    def assertNotificationNotReceived(self, user, notifying, type, expected_text=None):
        """
        Checks to make sure that a particular notification was not received by the user
        """
        self.assertReceivedNotificationCount(user, notifying, type, expected_text, expected_count=0)

    def assertNotificationTextEqual(self, notifying, notification, expected):
        actual = notifying.get_notification_text(notification)
        self.assertEqual(actual, expected, "Notification text not equal to expectation : %s" % actual)

    def assertNotificationTextNotEqual(self, notifying, notification, expected):
        self.assertNotEqual(notifying.get_notification_text(notification), expected, "Notification text equal to value that it shouldn't be.")


class TasksNotificationTestCase(NotificationTestCase):

    def test_comment_on_task(self):
        """
        Test comment notifications delivery from task
        """
        task = get_mock_task(self.project, self.jill)
        task.add_comment(self.bob, "Bob waz here.")
        self.assertNotificationReceived(self.jill, task, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on task \"%s\"" % task.title)
        self.assertNotificationNotReceived(self.bob, task, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on task \"%s\"" % task.title)
        task.add_comment(self.jill, "Ok, Bob.")
        self.assertNotificationReceived(self.bob, task, NOTIFICATION_TYPE_COMMENT_ADDED, "Jill commented on task \"%s\"" % task.title)
        self.assertNotificationNotReceived(self.jill, task, NOTIFICATION_TYPE_COMMENT_ADDED, "Jill commented on task \"%s\"" % task.title)

    def test_multiple_comments_on_task(self):
        """
        Test multiple comments by one user, notifications should update instead of creating new notifications
        """
        task = get_mock_task(self.project, self.jill)
        task.add_comment(self.bob, "Bob waz here.")
        task.add_comment(self.jill, "Bob waz here.")
        task.add_comment(self.bob, "Bob waz here.")
        # Jill should only have one notification from Bob
        self.assertNotificationReceived(self.jill, task, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on task \"%s\"" % task.title)

    def test_task_posted_with_parent(self):
        """
        Test notifications when task is posted with a parent solution,
        notify solution owner, if it is not same person who posted the task
        """
        self.ted = get_mock_user("ted", first_name="Ted")  # he is the project admin
        self.project.admin_set.add(self.ted)
        self.project.save()

        parent_solution = get_mock_solution(self.project, self.jill, title="Wood Floor", is_completed=False, is_closed=False)
        jill_task = get_mock_task(self.project, self.jill, solution=parent_solution, is_accepted=False, is_closed=False)
        self.assertNotificationNotReceived(self.jill, jill_task, NOTIFICATION_TYPE_TASK_POSTED)  # don't notify yourself
        self.assertNotificationNotReceived(self.ted, jill_task, NOTIFICATION_TYPE_TASK_POSTED)
        self.assertNotificationNotReceived(self.bob, jill_task, NOTIFICATION_TYPE_TASK_POSTED)

        task = get_mock_task(self.project, self.bob, solution=parent_solution, is_accepted=False, is_closed=False)
        self.assertNotificationReceived(self.jill, task, NOTIFICATION_TYPE_TASK_POSTED, "Bob posted a task on your solution \"%s\"" % parent_solution.default_title)
        self.assertNotificationNotReceived(self.ted, task, NOTIFICATION_TYPE_TASK_POSTED)
        self.assertNotificationNotReceived(self.bob, task, NOTIFICATION_TYPE_TASK_POSTED)

    def test_task_posted_no_parent(self):
        """
        Test notifications when task is posted without parents,
        notify project admins, excluding the person who posted the task, if an admin
        """
        self.project.admin_set.add(self.jill)
        self.ted = get_mock_user("ted", first_name="Ted")  # test with multiple project admins
        self.project.admin_set.add(self.ted)
        self.project.save()

        jill_task = get_mock_task(self.project, self.jill, is_accepted=False, is_closed=False)
        self.assertNotificationReceived(self.ted, jill_task, NOTIFICATION_TYPE_TASK_POSTED, "Jill posted a task")
        self.assertNotificationNotReceived(self.jill, jill_task, NOTIFICATION_TYPE_TASK_POSTED)  # don't notify yourself
        self.assertNotificationNotReceived(self.bob, jill_task, NOTIFICATION_TYPE_TASK_POSTED)

        task = get_mock_task(self.project, self.bob, is_accepted=False, is_closed=False)
        self.assertNotificationReceived(self.ted, task, NOTIFICATION_TYPE_TASK_POSTED, "Bob posted a task")
        self.assertNotificationReceived(self.jill, task, NOTIFICATION_TYPE_TASK_POSTED, "Bob posted a task")
        self.assertNotificationNotReceived(self.bob, task, NOTIFICATION_TYPE_TASK_POSTED)

    def test_task_accepted(self):
        """
        Test notifications when a regular task, created by the owner of a solution on a solution, is accepted
        """
        parent_solution = get_mock_solution(self.project, self.jill, title="Paint it Red", is_closed=False, is_completed=False)
        parent_task = get_mock_task(self.project, self.jill, is_closed=False, is_accepted=True)

        solution = get_mock_solution(self.project, self.bob, task=parent_task, is_closed=False, is_completed=False)
        task = get_mock_task(self.project, self.bob, solution=solution, is_closed=False, is_accepted=False )
        self.assertNotificationNotReceived(self.bob, task, NOTIFICATION_TYPE_TASK_POSTED)

        # Mark it accepted now
        task.mark_accepted(self.jill)
        self.assertNotificationReceived(self.bob, task, NOTIFICATION_TYPE_TASK_ACCEPTED,  "Your task \"%s\" was accepted" % task.title)

    def test_task_accepted_suggested(self):
        """
        Test notifications when a suggested task is accepted
        """
        solution = get_mock_solution(self.project, self.jill, title="Paint it Blue", is_closed=False, is_completed=False)
        task = get_mock_task(self.project, self.bob, solution=solution, is_closed=False, is_accepted=False)
        self.assertNotificationNotReceived(self.bob, task, NOTIFICATION_TYPE_TASK_ACCEPTED)
        self.assertNotificationNotReceived(self.jill, task, NOTIFICATION_TYPE_TASK_ACCEPTED)
        task.mark_accepted(self.jill)
        self.assertNotificationReceived(self.bob, task, NOTIFICATION_TYPE_TASK_ACCEPTED, "Your task \"%s\" was accepted" % task.title)
        self.assertNotificationNotReceived(self.jill, task, NOTIFICATION_TYPE_TASK_ACCEPTED)
        task.mark_unaccepted()  # should be removed now
        self.assertNotificationNotReceived(self.bob, task, NOTIFICATION_TYPE_TASK_ACCEPTED)
        self.assertNotificationNotReceived(self.jill, task, NOTIFICATION_TYPE_TASK_ACCEPTED)


class SolutionNotificationTestCase(NotificationTestCase):

    def test_solution_complete_for_task(self):
        """
        Test notification to task owner, when a solution for the task is marked complete
        """
        task = get_mock_task(self.project, self.jill, is_closed=False, is_accepted=True)
        solution = get_mock_solution(self.project, self.bob, task=task, is_completed=False, is_closed=False)
        solution.mark_complete()
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE, "Solution \"%s\" was marked complete" % solution.default_title)
        # Now mark incomplete and the notification should be gone
        solution.mark_incomplete()
        self.assertNotificationNotReceived(self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE)

    def test_solution_complete_for_closed_task(self):
        """
        Test notification to a closed task owner, when a solution for the task is marked complete
        since the task is closed there should be no notification
        """
        task = get_mock_task(self.project, self.jill, is_closed=True, is_accepted=True)
        solution = get_mock_solution(self.project, self.bob, task=task, is_completed=False, is_closed=False)
        solution.mark_complete()
        self.assertNotificationNotReceived(self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE)

    def test_solution_complete_same_owner(self):
        """
        Test notification to a task owner, who did contributed a solution to her own task and marked it complete
        should not receive notification
        """
        task = get_mock_task(self.project, self.jill, is_closed=False, is_accepted=True)
        solution = get_mock_solution(self.project, self.jill, task=task, is_completed=False, is_closed=False)
        solution.mark_complete()
        self.assertNotificationNotReceived(self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE)

    def test_solution_complete_has_votes(self):
        """
        Test notifications on a solution that was marked complete more then once,
        and maybe is reentering review - all users who previously voted for it
        should be notified and ask to re-review it and revise the vote
        """
        solution = get_mock_solution(self.project, self.bob, title="Making Jam", is_completed=False, is_closed=False)
        solution.mark_complete()  # solution marked complete for first time
        self.assertNotificationNotReceived(self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE)
        solution.put_vote(self.jill, 2)
        solution.mark_incomplete()  # something is wrong, marked incomplete to revise
        solution.mark_complete()
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE, "Solution \"%s\" was revised, update your vote" % solution.default_title)
        solution.mark_incomplete()  # notification should disappear
        self.assertNotificationNotReceived(self.jill, solution, NOTIFICATION_TYPE_SOLUTION_MARKED_COMPLETE)

    def test_solution_posted_with_parent_task(self):
        """
        Test notifications that a solution has been posted,
        if the solution has a parent task, notify parent task owner
        """
        self.ted = get_mock_user("ted", first_name="Ted")  # he is the project admin
        self.project.admin_set.add(self.ted)
        self.project.save()

        task = get_mock_task(self.project, self.jill, is_accepted=True, is_closed=False)
        jill_solution = get_mock_solution(self.project, self.jill, task=task, is_completed=False, is_closed=False)
        self.assertNotificationNotReceived(self.jill, jill_solution, NOTIFICATION_TYPE_SOLUTION_POSTED)  # don't notify yourself
        solution = get_mock_solution(self.project, self.bob, task=task, is_completed=False, is_closed=False)
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_SOLUTION_POSTED, "Bob posted a solution on your task \"%s\"" % task.title)
        self.assertNotificationNotReceived(self.bob, solution, NOTIFICATION_TYPE_SOLUTION_POSTED)
        self.assertNotificationNotReceived(self.ted, solution, NOTIFICATION_TYPE_SOLUTION_POSTED)  # no notification to the project admin

    def test_solution_posted_with_parent_solution(self):
        """
        Test notifications that a solution has been posted,
        if the solution has a parent solution, notify parent solution owner
        """
        self.ted = get_mock_user("ted", first_name="Ted")  # he is the project admin
        self.project.admin_set.add(self.ted)
        self.project.save()

        parent_solution = get_mock_solution(self.project, self.jill, title="Doodle", is_completed=False, is_closed=False)
        jill_solution = get_mock_solution(self.project, self.jill, solution=parent_solution, is_completed=False, is_closed=False)
        self.assertNotificationNotReceived(self.jill, jill_solution, NOTIFICATION_TYPE_SOLUTION_POSTED)  # don't notify yourself
        solution = get_mock_solution(self.project, self.bob, solution=parent_solution, is_completed=False, is_closed=False)
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_SOLUTION_POSTED, "Bob posted a solution on your solution \"%s\"" % parent_solution.default_title)
        self.assertNotificationNotReceived(self.bob, solution, NOTIFICATION_TYPE_SOLUTION_POSTED)
        self.assertNotificationNotReceived(self.ted, solution, NOTIFICATION_TYPE_SOLUTION_POSTED)  # no notification to the project admin

    def test_solution_posted_no_parent(self):
        """
        Test notifications that a solution has been posted,
        if the solution has no parents, notify the project administrators
        """
        self.project.admin_set.add(self.jill)
        self.ted = get_mock_user("ted", first_name="Ted")  # test with multiple project admins
        self.project.admin_set.add(self.ted)
        self.project.save()

        jill_solution = get_mock_solution(self.project, self.jill, is_completed=False, is_closed=False)
        self.assertNotificationNotReceived(self.jill, jill_solution, NOTIFICATION_TYPE_SOLUTION_POSTED) # don't notify yourself
        self.assertNotificationReceived(self.ted, jill_solution, NOTIFICATION_TYPE_SOLUTION_POSTED, "Jill posted a solution")
        solution = get_mock_solution(self.project, self.bob, is_completed=False, is_closed=False)
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_SOLUTION_POSTED, "Bob posted a solution")
        self.assertNotificationReceived(self.ted, solution, NOTIFICATION_TYPE_SOLUTION_POSTED, "Bob posted a solution")
        self.assertNotificationNotReceived(self.bob, solution, NOTIFICATION_TYPE_SOLUTION_POSTED)

    # Comments on solutions

    def test_comment_on_solution(self):
        """
        Test comment notifications delivery from solution
        """
        task = get_mock_task(self.project, self.jill)
        solution = get_mock_solution(self.project, self.jill, task=task)
        solution.add_comment(self.bob, "Bob waz here.")
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(self.bob, solution, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on solution \"%s\"" % solution.default_title)
        solution.add_comment(self.jill, "Ok, Bob.")
        self.assertNotificationReceived(self.bob, solution, NOTIFICATION_TYPE_COMMENT_ADDED, "Jill commented on solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(self.jill, solution, NOTIFICATION_TYPE_COMMENT_ADDED, "Jill commented on solution \"%s\"" % solution.default_title)
        # Make sure it is giving you the default title
        solution.title = "MY TITLE"
        solution.save()
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on solution \"MY TITLE\"")
        self.assertNotificationReceived(self.bob, solution, NOTIFICATION_TYPE_COMMENT_ADDED, "Jill commented on solution \"MY TITLE\"")

    # Votes on solution

    def test_vote_on_solution(self):
        """
        Test notifications for votes on solution
        """
        self.ted = get_mock_user("ted", first_name="Ted")
        solution = get_mock_solution(self.project, self.jill, title="Cleaning up")
        solution.put_vote(self.bob, 2)
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_VOTE_ADDED, "Bob voted on your solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(self.bob, solution, NOTIFICATION_TYPE_VOTE_ADDED, "Bob voted on your solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(self.ted, solution, NOTIFICATION_TYPE_VOTE_ADDED, "Bob voted on your solution \"%s\"" % solution.default_title)
        time.sleep(1)  # so that the voting order is established, which effect notification text
        solution.put_vote(self.ted, 0)
        debug_votes(solution)
        # Check that only one notification should just update
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_VOTE_ADDED, "Ted and Bob voted on your solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(self.bob, solution, NOTIFICATION_TYPE_VOTE_ADDED, "Ted and Bob voted on your solution \"%s\"" % solution.default_title)
        self.assertNotificationNotReceived(self.ted, solution, NOTIFICATION_TYPE_VOTE_ADDED, "Ted and Bob voted on your solution \"%s\"" % solution.default_title)

    def test_vote_updated_on_solution(self):
        """
        Tests notifications when votes are updated on a solution
        """
        solution = get_mock_solution(self.project, self.jill, title="Cleaning up")
        solution.put_vote(self.bob, 0)
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_VOTE_ADDED, "Bob voted on your solution \"%s\"" % solution.default_title)
        solution.put_vote(self.bob, 0)  # same vote, check that updated notification is not sent
        self.assertNotificationNotReceived(self.jill, solution, NOTIFICATION_TYPE_VOTE_UPDATED, "Bob updated a vote on your solution \"%s\"" % solution.default_title)
        solution.put_vote(self.bob, 2)
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_VOTE_UPDATED, "Bob updated a vote on your solution \"%s\"" % solution.default_title)
        solution.put_vote(self.bob, 1)  # check that it creates another notification todo
        self.assertReceivedNotificationCount(self.jill, solution, NOTIFICATION_TYPE_VOTE_UPDATED, "Bob updated a vote on your solution \"%s\"" % solution.default_title, expected_count=2)


class CommentNotificationTestCase(NotificationTestCase):

    def test_vote_on_comment(self):
        """
        Tests notifications for votes on comments,
        should only notify when someone marked there comment helpful
        """
        self.ted = get_mock_user("ted", first_name="Ted")
        self.katy = get_mock_user("katy", first_name="Katy")
        solution = get_mock_solution(self.project, self.jill, title="Cleaning up")
        comment = solution.add_comment(self.bob, "You should add some tests.")
        comment.put_vote(self.ted, 0)  # negative vote on comment should not trigger notification
        self.assertNotificationNotReceived(self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL)
        comment.put_vote(self.katy, 2)
        self.assertNotificationReceived(self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL, "Katy marked your comment helpful")
        time.sleep(1)
        comment.put_vote(self.jill, 1)
        self.assertNotificationReceived(self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL, "Jill and Katy marked your comment helpful")
        debug_votes(comment)

    def test_vote_regular_update_on_comment(self):
        """
        Tests notifications when votes are updated on a comment
        with out changing is_accepted state
        """
        solution = get_mock_solution(self.project, self.jill, title="Cleaning up")
        comment = solution.add_comment(self.bob, "You should add some tests.")
        comment.put_vote(self.jill, 2)
        self.assertNotificationReceived(self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL, "Jill marked your comment helpful")
        comment.put_vote(self.jill, 1)
        self.assertNotificationReceived(self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL, "Jill marked your comment helpful")

    def test_vote_negative_update_on_comment(self):
        """
        Test notification when a vote on a comment goes from accepted to unaccepted
        """
        self.ted = get_mock_user("ted", first_name="Ted")
        solution = get_mock_solution(self.project, self.jill, title="Cleaning up")
        comment = solution.add_comment(self.bob, "You should add some tests.")
        comment.put_vote(self.jill, 2)
        self.assertNotificationReceived(self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL, "Jill marked your comment helpful")
        time.sleep(1)  # to get correct order when sorting by time voted
        comment.put_vote(self.ted, 1)
        self.assertNotificationReceived(self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL, "Ted and Jill marked your comment helpful")
        comment.put_vote(self.jill, 0)  # notification still be there
        self.assertNotificationReceived(self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL, "Ted marked your comment helpful")
        comment.put_vote(self.ted, 0)  # notification should now be gone as there are no positive votes left
        self.assertNotificationNotReceived(self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL)

    def test_vote_positive_update_on_comment(self):
        """
        Tests notifications when a vote on a comment goes from unaccepted to accepted
        """
        solution = get_mock_solution(self.project, self.jill, title="Cleaning up")
        comment = solution.add_comment(self.bob, "You should add some tests.")
        comment.put_vote(self.jill, 0)
        self.assertNotificationNotReceived(self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL)
        comment.put_vote(self.jill, 2)  # now accepted, should remove notification above
        self.assertNotificationReceived(self.bob, comment, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL)