""" View related tests for core app. """
from django.test.testcases import TestCase

from joltem.libs import mixer


class TestJoltemViews(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.project = mixer.blend('project.project')
        cls.user = mixer.blend('joltem.user', password='test')

    def test_home(self):
        self.client.login(username=self.user.username, password='test')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)

    def test_notifications(self):
        for _ in range(2):
            task = mixer.blend('task.task', author=self.user, owner=self.user)
            guest = mixer.blend('joltem.user')
            task.add_comment(guest, mixer.g.get_string())

            solution = mixer.blend('solution.solution', task=task,
                                   author=self.user, owner=self.user)
            solution.add_comment(guest, mixer.g.get_string())

        self.assertEqual(self.user.notification_set.count(), 4)

        self.client.login(username=self.user.username, password='test')
        with self.assertNumQueries(10):
            response = self.client.get('/notifications/')
        self.assertContains(response, guest.first_name)
