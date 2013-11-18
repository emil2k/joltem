# coding: utf-8

""" Factories for tests. """

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "joltem.settings.local")

import factory

from joltem.models import User
from project.models import Project
from git.models import Repository


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
