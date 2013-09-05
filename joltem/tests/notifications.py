from django.test import TestCase
from django.contrib.contenttypes.generic import ContentType


from joltem.tests import TestCaseDebugMixin, TEST_LOGGER
from joltem.tests.mocking import *

from joltem.models.notifications import Notification
from joltem.models.comments import NOTIFICATION_TYPE_COMMENT_ADDED


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

    def assertNotificationReceived(self, user, notifying, type, expected_text=None):
        """
        Checks if a notification was received by the user, from the notifying instance
        if expected text is passed checks that the text matches also
        """
        notifying_type = ContentType.objects.get_for_model(notifying)
        try:
            notification = user.notification_set.get(
                user_id=user.id,
                notifying_type_id=notifying_type.id,
                notifying_id=notifying.id,
                type=type
            )
            if expected_text:
                self.assertNotificationTextEqual(notifying, notification, expected_text)
        except Notification.DoesNotExist, e:
            self.fail("Notification was not received.")
        except Notification.MultipleObjectsReturned, e:
            TEST_LOGGER.debug("NOTIFICATIONS FOUND (all): %d" % Notification.objects.all().count())
            self.fail("Multiple notifications received of the same type from the same instance.")

    def assertNotificationNotReceived(self, user, notifying, type, expected_text=None):
        """
        Checks to make sure that a particular notification was not received by the user
        """
        notifying_type = ContentType.objects.get_for_model(notifying)
        notifications = user.notification_set.filter(
            user_id=user.id,
            notifying_type_id=notifying_type.id,
            notifying_id=notifying.id,
            type=type
        )
        try:
            for notification in notifications:
                self.assertNotificationTextNotEqual(notifying, notification, expected_text)
        except AssertionError, e:
            self.fail("Notification was received when it should not have been.")

    def assertNotificationTextEqual(self, notifying, notification, expected):
        self.assertEqual(notifying.get_notification_text(notification), expected, "Notification text not equal to expectation.")

    def assertNotificationTextNotEqual(self, notifying, notification, expected):
        self.assertNotEqual(notifying.get_notification_text(notification), expected, "Notification text equal to value that it shouldn't be.")

    # Tests

    def test_comment_on_task(self):
        """
        Test comment notifications delivery from task
        """
        task = get_mock_task(self.project, self.jill)
        task.add_comment(self.bob, "Bob waz here.")
        self.assertNotificationReceived(self.jill, task, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on task %s" % task.title)
        self.assertNotificationNotReceived(self.bob, task, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on task %s" % task.title)
        task.add_comment(self.jill, "Ok, Bob.")
        self.assertNotificationReceived(self.bob, task, NOTIFICATION_TYPE_COMMENT_ADDED, "Jill commented on task %s" % task.title)
        self.assertNotificationNotReceived(self.jill, task, NOTIFICATION_TYPE_COMMENT_ADDED, "Jill commented on task %s" % task.title)

    def test_comment_on_solution(self):
        """
        Test comment notifications delivery from solution
        """
        task = get_mock_task(self.project, self.jill)
        solution = get_mock_solution(self.project, self.jill, task=task)
        solution.add_comment(self.bob, "Bob waz here.")
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on solution %s" % solution.default_title)
        self.assertNotificationNotReceived(self.bob, solution, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on solution %s" % solution.default_title)
        solution.add_comment(self.jill, "Ok, Bob.")
        self.assertNotificationReceived(self.bob, solution, NOTIFICATION_TYPE_COMMENT_ADDED, "Jill commented on solution %s" % solution.default_title)
        self.assertNotificationNotReceived(self.jill, solution, NOTIFICATION_TYPE_COMMENT_ADDED, "Jill commented on solution %s" % solution.default_title)
        # Make sure it is giving you the default title
        solution.title = "MY TITLE"
        solution.save()
        self.assertNotificationReceived(self.jill, solution, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on solution MY TITLE")
        self.assertNotificationReceived(self.bob, solution, NOTIFICATION_TYPE_COMMENT_ADDED, "Jill commented on solution MY TITLE")



    def test_multiple_comments_on_task(self):
        """
        Test multiple comments by one user, notifications should update instead of creating new notifications
        """
        task = get_mock_task(self.project, self.jill)
        task.add_comment(self.bob, "Bob waz here.")
        task.add_comment(self.jill, "Bob waz here.")
        task.add_comment(self.bob, "Bob waz here.")
        # Jill should only have one notification from Bob
        self.assertNotificationReceived(self.jill, task, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on task %s" % task.title)
