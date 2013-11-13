""" Form related tests for the core app. """

from django.test import TestCase
from django.core.exceptions import ValidationError
from joltem.forms.utils import validate_username_available, validate_username
from joltem.libs.mock.models import get_mock_user


class ValidateUsernameTest(TestCase):

    """ Test for validator that checks whether username is valid. """

    def test_valid(self):
        """ Test simple valid username. """
        try:
            validate_username('bill')
        except ValidationError:
            self.fail("Username should be valid.")

    def test_invalid(self):
        """ Test username with invalid characters. """
        with self.assertRaises(ValidationError):
            validate_username('ke$ha')

    def test_no_hyphens(self):
        """ Test that hyphens are not allowed in usernames. """
        with self.assertRaises(ValidationError):
            validate_username('i-am-bill')


class ValidateUsernameAvailableTest(TestCase):

    """ Test for validator that checks whether username is available. """

    def test_available(self):
        """ Test available username. """
        try:
            validate_username_available('bill')
        except ValidationError:
            self.fail('Username should be available.')

    def test_taken(self):
        """ Test a previously taken username. """
        get_mock_user('bill')
        with self.assertRaises(ValidationError):
            validate_username_available('bill')



