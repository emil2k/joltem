from django.test import TestCase

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
        self.ted = get_mock_user("ted", first_name="Ted")

    # Custom assertions

    def assertNotificationReceived(self, user, notifying, type, expected_text=None):
        """
        Checks if a notification was received by the user, from the notifying instance
        if expected text is passed checks that the text matches also
        """
        from django.contrib.contenttypes.generic import ContentType
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
            self.fail("Multiple notifications received of the same type from the same instance")

    def assertNotificationTextEqual(self, notifying, notification, expected):
        self.assertEqual(notifying.get_notification_text(notification), expected)

    # Tests

    def test_comment_on_task(self):
        """
        Test comments on a task
        """
        task = get_mock_task(self.project, self.jill)
        task.add_comment(self.bob, "Bob waz here.")
        self.assertNotificationReceived(self.jill, task, NOTIFICATION_TYPE_COMMENT_ADDED, "Bob commented on task %s" % task.title)


