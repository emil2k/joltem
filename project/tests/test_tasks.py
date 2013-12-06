from django.test.testcases import TestCase
from joltem.libs.mix import mixer
from project.tasks import prepare_activity_feeds
from ..models import Project
from django.core import mail


class ProjectTasksTestCase(TestCase):

    def setUp(self):
        self.projects = mixer.cycle(2).blend(Project, subscriber_set=[])
        self.users = mixer.cycle(4).blend('joltem.user')

        mixer.cycle(3).blend(
            'solution.solution', project=mixer.random(*self.projects),
            owner=mixer.random(*self.users))

        tasks = mixer.cycle(3).blend(
            'task.task', project=mixer.random(*self.projects),
            owner=mixer.random(*self.users))

        mixer.cycle(3).blend(
            'joltem.comment', project=mixer.random(*self.projects),
            comment=mixer.random, owner=mixer.random(*self.users),
            commentable=mixer.random(*tasks))

    def test_activity_feed(self):
        prepare_activity_feeds()
        self.assertFalse(mail.outbox)

        project = self.projects[0]
        project.subscriber_set = self.users[:2]

        prepare_activity_feeds()

        self.assertEqual(len(mail.outbox), 2)
        mm = mail.outbox.pop()
        self.assertTrue(project.title in mm.body)
