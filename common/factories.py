# coding: utf-8
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "joltem.settings")

import factory
from django.contrib.auth.models import User

from project.models import Project
from git.models import Repository


class UserF(factory.DjangoModelFactory):

    FACTORY_FOR = User

    username = factory.Sequence(lambda num: u'jon_snow{}'.format(num))
    first_name = factory.Sequence(lambda num: u'Jon{}'.format(num))
    last_name = factory.Sequence(lambda num: u'Snow{}'.format(num))
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

    FACTORY_FOR = Project

    name = factory.Sequence(lambda num: u'joltem{}'.format(num))
    title = factory.Sequence(lambda num: u'Joltem{}'.format(num))


class RepositoryF(factory.DjangoModelFactory):

    FACTORY_FOR = Repository

    project = factory.SubFactory(ProjectF)
    name = factory.Sequence(lambda num: u'repo{}'.format(num))


def init_joltem_project():
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
