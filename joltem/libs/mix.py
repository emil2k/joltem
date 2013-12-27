""" Prepare mixer to generate Joltem models. """
from mixer.backend.django import mixer

from git.models import Authentication
from joltem.models import User
from project.models import Project


def _set_password(user):
    user.set_password(user.password)
    return user

mixer.register(User, {}, postprocess=_set_password)

mixer.register(Project, {
    'name': mixer.f.get_simple_username
})

mixer.register(Authentication, {
    'key': lambda: 'ssh-rsa %s %s' % (
        mixer.g.get_string(length=372), mixer.f.get_email()),
})
