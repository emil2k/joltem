""" Factories for tests. """

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "joltem.settings.local")

import factory
import factory.fuzzy

from joltem.models import User
from project.models import Project
from git.models import Repository, Authentication
from task.models import Task
from solution.models import Solution


class UserF(factory.DjangoModelFactory):

    """ Generate users. """

    FACTORY_FOR = User

    username = factory.Sequence(u'jon_snow{}'.format)
    first_name = factory.Sequence(u'Jon{}'.format)
    last_name = factory.Sequence(u'Snow{}'.format)
    email = factory.LazyAttribute(
        lambda obj: u'{}@example.org'.format(obj.username))
    is_staff = False
    is_superuser = False
    is_active = True
    password = '123'

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserF, cls)._prepare(create, **kwargs)

        if password:
            user.set_password(password)
            if create:
                user.save()
        return user


class ProjectF(factory.DjangoModelFactory):

    """ Generate projects. """

    FACTORY_FOR = Project

    name = factory.Sequence(u'joltem{}'.format)
    title = factory.Sequence(u'Joltem{}'.format)


class RepositoryF(factory.DjangoModelFactory):

    """ Generate repositories. """

    FACTORY_FOR = Repository

    project = factory.SubFactory(ProjectF)
    name = factory.Sequence(u'repo{}'.format)


class AuthenticationF(factory.DjangoModelFactory):

    """ Generate authentication. """

    FACTORY_FOR = Authentication

    user = factory.SubFactory(UserF)
    name = factory.Sequence(u'ssh-key-{}'.format)
    key = (
        "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAGEArzJx8OYOnJmzf4tfBE"
        "vLi8DVPrJ3/c9k2I/Az64fxjHf9imyRJbixtQhlH9lfNjUIx+4LmrJH"
        "5QNRsFporcHDKOTwTTYLh5KmRpslkYHRivcJSkbh/C+BR3utDS555mV comment"
    )
    fingerprint = '3d:13:5f:cb:c9:79:8a:93:06:27:65:bc:3d:0b:8f:af'


class TaskF(factory.DjangoModelFactory):

    """ Generate tasks. """

    FACTORY_FOR = Task

    owner = factory.SubFactory(UserF)
    author = factory.SubFactory(UserF)
    title = factory.Sequence(u'task{}'.format)
    priority = factory.fuzzy.FuzzyInteger(Task.LOW_PRIORITY, Task.HIGH_PRIORITY)


class SolutionF(factory.DjangoModelFactory):

    """ Generate mock solution. """

    FACTORY_FOR = Solution

    owner = factory.SubFactory(UserF)
    project = factory.SubFactory(ProjectF)


def init_joltem_project():
    """ Setup project and some users. """

    if Project.objects.filter(pk=1).exists():
        return

    joltem_project = ProjectF(pk=1, name='joltem', title='Joltem')

    RepositoryF(project=joltem_project, name='main',
                description='Website and current git server setup.')

    UserF(username='emil', first_name='Emil', is_staff=True, is_superuser=True)
    UserF(username='bob', first_name='Bob')
    UserF(username='jill', first_name='Jill')
    UserF(username='kate', first_name='Kate')
    UserF(username='ian', first_name='Ian')
    UserF(username='will', first_name='Will')
    UserF(username='becky', first_name='Becky')


if __name__ == '__main__':
    init_joltem_project()
