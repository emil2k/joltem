""" Test forms and validator for main Joltem app. """

from django.core.exceptions import ValidationError
from django.test import TestCase
from joltem.libs import mixer

from ..forms import validate_username

class ValidatorTest(TestCase):

    """ Test validators. """

    def test_validate_username_valid(self):
        """ Test valid username. """
        user = mixer.blend('joltem.user', username='jill')
        try:
            validate_username('jill')
        except ValidationError:
            self.fail("Threw a validation error, when should be valid")

    def test_validate_username_invalid(self):
        """ Test invalid username. """
        with self.assertRaisesMessage(ValidationError,
                                      'There is no user with that username.'):
            validate_username('bob')

    def test_validate_username_blank(self):
        """ Test blank username. """
        with self.assertRaisesMessage(ValidationError,
                                      'Username not provided.'):
            validate_username('')

    def test_validated_username_none(self):
        """ Test None username. """
        with self.assertRaisesMessage(ValidationError,
                                      'Username not provided.'):
            validate_username(None)