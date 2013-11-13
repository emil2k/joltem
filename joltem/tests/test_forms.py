""" Form related tests for the core app. """

import unittest
from django.test import TestCase
from django.core.exceptions import ValidationError
from joltem.forms import SignUpForm
from joltem.forms.utils import validate_username_available, validate_username
from joltem.libs.mock.models import get_mock_user


class SignUpFormTest(unittest.TestCase):

    """ Test sign up form. """

    def _test_passwords_matching(self, match):
        """ Test password matching enforcement.

        :param match: whether passwords should match.

        """
        password = 'bill2bill'
        password_confirm = password if match else password + "oops"
        data = {
            'invite_code': 'dummycode',
            'username': 'bill',
            'first_name': 'Billy',
            'email': 'bill@gmail.com',
            'password': password,
            'password_confirm': password_confirm,
        }
        form = SignUpForm(data)
        self.assertEqual(form.is_valid(), match)

    def test_passwords_match(self):
        """ Test case where passwords match. """
        self._test_passwords_matching(True)

    def test_passwords_no_match(self):
        """ Test case where passwords don't match. """
        self._test_passwords_matching(False)


class ValidateUsernameTest(unittest.TestCase):

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



