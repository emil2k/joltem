from django.test import TestCase
from joltem.libs import mixer


class JoltemTestVoteBase(TestCase):

    def test_solution_vote(self):
        project = mixer.blend('project.project', title='Joltem')

        user = mixer.blend('joltem.user', username='user')
        self.assertEqual(user.impact_set.count(), 0)
        self.assertEqual(user.get_impact(), 0)

        solution = mixer.blend(
            'solution.solution', project=project, owner=user)
        solution.mark_complete(100)
        self.assertEqual(user.impact_set.count(), 1)
        self.assertEqual(user.get_impact(), 0)

        voter1 = mixer.blend('joltem.user', username='voter1')
        solution.add_vote(voter1, True)
        self.assertEqual(user.get_impact(), 0)

        voter2 = mixer.blend('joltem.user', username='voter2', impact=1)
        solution.add_vote(voter2, True)
        self.assertEqual(user.get_impact(), 100)
