""" Form related utilities. """

import re
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

username_re = re.compile(r'^[a-zA-Z0-9_]+$')

def validate_username(username):
    """ Validate that passed username is valid.

    Username must contain numbers, letters, or underscores.
    This does not enforce length constraints, use the field to
    enforce those.

    :param username: check if valid
    :return: nothing if available, raise ValidationError otherwise.

    """
    v = RegexValidator(
        username_re,
        u'Enter a valid username consisting of letters, numbers, '
        u'or underscores.',
        'invalid')
    return v(username)

def validate_username_available(username):
    """ Validate that username is available to sign up with.

    :param username: check if this is available.
    :return: nothing if available, raise ValidationError otherwise.

    """
    if User.objects.filter(username=username).exists():
        raise ValidationError('The username is taken.', 'taken')