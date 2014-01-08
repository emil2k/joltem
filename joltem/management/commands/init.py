""" Fill initial data. """

from django.core.management import BaseCommand


class Command(BaseCommand):

    """ Create initial data. """

    def handle(self, *args, **kwargs):
        """ Handle command.

        :returns: False

        """

        from joltem.libs import mixer
        from project.models import Project
        from joltem.models import User

        if Project.objects.count():
            return False

        with mixer.ctx(loglevel='DEBUG'):

            root = mixer.blend(
                User, username='root', is_superuser=True,
                first_name='John', last_name='Konor',
                is_staff=True, password='root')

            project = mixer.blend(Project, name='Joltem', title='Joltem')
            project.admin_set = [root]

            mixer.blend('git.repository', project=project)

            users = mixer.cycle(5).blend(User)

            tasks = mixer.cycle(20).blend(
                'task.task',
                project=project,
                author=mixer.RANDOM(*users),
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
