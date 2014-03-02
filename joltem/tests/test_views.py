""" View related tests for core app. """
from django.test.testcases import TestCase
from django.core.urlresolvers import reverse
from joltem.libs import mixer


class TestJoltemViews(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.project = mixer.blend('project.project')
        cls.user = mixer.blend('joltem.user', password='test',
                               first_name='Jane')

    def test_home(self):
        self.client.login(username=self.user.username, password='test')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_user(self):
        """ Test GET of user profile page.

        Test to make sure the right user's profile is showing and test that
        the title is set properly.

        """
        self.client.login(username=self.user.username, password='test')
        profiled = mixer.blend('joltem.user', username='bill1978',
                               first_name='Billy', last_name="Bob")
        comment = mixer.blend('joltem.comment', owner=profiled)
        solution1 = mixer.blend(
            'solution.solution', owner=profiled, title=mixer.RANDOM)
        solution2 = mixer.blend(
            'solution.solution', owner=profiled, is_completed=True,
            is_closed=True, task=mixer.RANDOM)
        response = self.client.get(reverse(
            'user', args=[profiled.username]))
        self.assertContains(response, 'Billy')
        self.assertContains(response, '<title>Billy Bob - Joltem</title>')
        self.assertContains(response, solution1.title)
        self.assertContains(response, solution2.default_title)
        self.assertContains(response, comment.comment)

    def test_notifications(self):
        for _ in range(2):
            task = mixer.blend('task.task', owner=self.user)
            guest = mixer.blend('joltem.user')
            task.add_comment(guest, mixer.G.get_string())

            solution = mixer.blend(
                'solution.solution', task=task, owner=self.user)
            solution.add_comment(guest, mixer.G.get_string())

        self.assertEqual(self.user.notification_set.count(), 4)

        self.client.login(username=self.user.username, password='test')
        with self.assertNumQueries(10):
            response = self.client.get('/notifications/')
        self.assertContains(response, guest.first_name)

        self.user.notifications = self.user.notification_set.filter(
            is_cleared=False).count()
        self.assertTrue(self.user.notifications)
        self.user.save()

        with self.assertNumQueries(5):
            response = self.client.post('/notifications/', data=dict(
                clear_all=True))
        self.assertFalse(
            self.user.notification_set.filter(is_cleared=False).count())
        self.user = type(self.user).objects.get(pk=self.user.pk)
        self.assertFalse(self.user.notifications)
