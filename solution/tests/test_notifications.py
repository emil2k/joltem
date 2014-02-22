from django.test import TestCase
from django.core.urlresolvers import reverse
from joltem.libs import mixer


class SolutionTestNotifications(TestCase):

    def test_clear_notifications(self):
        manager = mixer.blend(
            'joltem.user', username='manager', password='manager')
        solution = mixer.blend('solution.solution', owner=manager)

        user = mixer.blend('joltem.user')
        solution.add_comment(user, 'comment')
        solution.add_vote(user, True)

        self.assertTrue(manager.notification_set.all())
        self.assertFalse(manager.notification_set.filter(is_cleared=True))

        self.client.login(username='manager', password='manager')
        path = reverse('project:solution:solution', args=[
            solution.project_id, solution.id
        ])
        self.client.get(path)

        self.assertFalse(manager.notification_set.filter(is_cleared=False))
