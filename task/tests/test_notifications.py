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

        voter = mixer.blend('user')
        task.put_vote(voter, True)
        self.assertEqual(len(task.followers), 4)

        task.put_vote(task.author, True)
        self.assertEqual(len(task.followers), 4)

    def test_review(self):
        task = mixer.blend('task.task', project=self.project)
        acceptor = mixer.blend('user')
        task.mark_reviewed(acceptor, True)
        self.assertTrue(task.author.notification_set.exists())
        self.assertFalse(acceptor.notification_set.exists())

    def test_vote(self):
        task = mixer.blend('task.task', project=self.project)

        voter = mixer.blend('user')
        task.put_vote(voter, True)
        self.assertFalse(voter.notification_set.all())
        self.assertTrue(task.author.notification_set.all())
        self.assertTrue(task.owner.notification_set.all())

        notify = task.author.notification_set.first()
        self.assertEqual("%s voted on your task \"%s\"" % (
            voter.first_name, task.title
        ), notify.get_text())

        task.put_vote(voter, False)
        notify = task.author.notification_set.last()
        self.assertEqual("%s updated a vote on your task \"%s\"" % (
            voter.first_name, task.title
        ), notify.get_text())
