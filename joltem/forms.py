""" Forms and validators for Joltem app. """

from django.core.exceptions import ValidationError
from .models import User


def validate_username(username):
    """ Validator for username.

    Checks if the username matches a real user, raises ValidationError.

    :param username:

    """
    if username:
        if not User.objects.filter(username=username).exists():
            raise ValidationError('There is no user with that username.')
    else:
        raise ValidationError('Username not provided.')