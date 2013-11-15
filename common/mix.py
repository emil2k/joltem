""" Prepare mixer to generate Joltem models. """

from mixer.backend.django import mixer
from project.models import Project
from joltem.models import User


mixer.register(Project, {
    'name': mixer.f.get_simple_username
})


def _set_password(user):
    user.set_password(user.password)
    return user

mixer.register(User, {}, postprocess=_set_password)
