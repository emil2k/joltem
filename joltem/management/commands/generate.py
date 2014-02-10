""" Fill initial data. """

from django.core.management import BaseCommand


class Command(BaseCommand):

    """ Generate initial data. """

    def handle(self, *args, **kwargs):
        """ Handle command.

        TODO: Support arguments ('tasks', 'solutions', 'users')

        :returns: False

        """

        from joltem.libs import mixer
        from joltem.models import User
        from task.models import Task

        with mixer.ctx(loglevel='DEBUG'):

            root = mixer.guard(username='root').blend(
                User, is_superuser=True, first_name='John',
                last_name='Konor', is_staff=True, password='root')

            manager = mixer.guard(username='manager').blend(
                User, first_name='Marilyn', last_name='Monroe',
                password='manager')

            developer = mixer.guard(username='developer').blend(
                User, first_name='Abraham', last_name='Lincoln',
                password='developer')

            mixer.guard(username='user').blend(
                User, username='user', first_name='James',
                last_name='Bond', password='user')

            project = mixer.guard(title='Joltem').blend('project.project')
            project.admin_set = [root]
            project.manager_set = [manager]
            project.developer_set = [developer]

            mixer.guard(project=project).blend('git.repository')

            if not Task.objects.exists():

                users = mixer.cycle(5).blend(User)

                tasks = mixer.cycle(20).blend(
                    'task.task',
                    project=project,
                    owner=mixer.RANDOM(*users),
                    is_completed=mixer.RANDOM,
                    is_closed=mixer.RANDOM,
                )

                solutions = mixer.cycle(10).blend(
                    'solution.solution',
                    project=project,
                    owner=mixer.RANDOM(*users),
                    is_completed=mixer.RANDOM,
                    is_closed=mixer.RANDOM,
                    task=mixer.SELECT,
                )

                mixer.cycle(15).blend(
                    'joltem.comment',
                    owner=mixer.RANDOM(*users),
                    comment=mixer.RANDOM,
                    project=project,
                    commentable=mixer.RANDOM(*(tasks + solutions))
                )
