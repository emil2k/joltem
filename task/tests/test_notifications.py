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
