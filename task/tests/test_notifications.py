from django.test import TestCase
from joltem.libs import mixer


class TaskNotificationsTest(TestCase):

    def setUp(self):
        self.project = mixer.blend('project.project')

    def test_meta(self):
        """ Check loading a task notification interfaces. """

        from joltem.notifications import get_notify

        task = mixer.blend('task.task')
        notification = mixer.blend('joltem.notification',
                                   notifiyng=task, type='comment_added')
        nn = get_notify(notification, task)
        self.assertTrue(nn)

    def test_get_followers(self):
        """ Check task's followers. """

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

        voter = mixer.blend('user')
        task.put_vote(voter, True)

        acceptor = mixer.blend('user')
        task.mark_reviewed(acceptor, True)

        notify = task.author.notification_set.last()
        self.assertEqual(
            notify.get_text(), 'Your task "%s" was accepted' % task.title)
        notify = voter.notification_set.last()
        self.assertEqual(
            notify.get_text(), 'Task "%s" was accepted' % task.title)

    def test_vote(self):
        task = mixer.blend('task.task', project=self.project)

        voter1 = mixer.blend('user')
        task.put_vote(voter1, True)

        self.assertFalse(voter1.notification_set.all())
        self.assertTrue(task.author.notification_set.all())
        self.assertTrue(task.owner.notification_set.all())

        notify = task.author.notification_set.first()
        self.assertEqual("%s voted on your task \"%s\"" % (
            voter1.first_name, task.title
        ), notify.get_text())

        task.put_vote(voter1, False)

        notify = task.author.notification_set.last()
        self.assertEqual("%s updated a vote on your task \"%s\"" % (
            voter1.first_name, task.title
        ), notify.get_text())

        voter2 = mixer.blend('user')
        task.put_vote(voter2, False)
        notify = voter1.notification_set.get()
        self.assertEqual(notify.get_text(), '%s voted on task "%s"' % (
            voter2.first_name, task.title))

        voter3 = mixer.blend('user')
        task.put_vote(voter3, False)
        self.assertEqual(notify.get_text(), '%s and %s voted on task "%s"' % (
            voter2.first_name, voter3.first_name, task.title))

        task.put_vote(voter3, False)
        self.assertEqual(notify.get_text(), '%s and %s voted on task "%s"' % (
            voter2.first_name, voter3.first_name, task.title))
