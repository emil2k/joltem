from django.test import TestCase
from joltem.libs import mixer


class TaskNotificationsTest(TestCase):

    def setUp(self):
        self.project = mixer.blend('project.project')

    def test_get_followers(self):
        task = mixer.blend('task.task', project=self.project)
        self.assertEqual(len(task.followers), 2)

        mixer.blend('comment', commentable=task)
        self.assertEqual(len(task.followers), 3)

        mixer.blend('comment', commentable=task, owner=task.owner)
        self.assertEqual(len(task.followers), 3)

    def test_review(self):
        task = mixer.blend('task.task', project=self.project)
        acceptor = mixer.blend('user')
        task.mark_reviewed(acceptor, True)
        self.assertTrue(task.author.notification_set.exists())
        self.assertFalse(acceptor.notification_set.exists())
