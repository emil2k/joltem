""" Form related tests for the core app. """

import unittest

from joltem.forms.utils import is_valid_email

class ValidEmailTest(unittest.TestCase):

    """ Test email validation utility. """

    def test_valid_email(self):
        self.assertTrue(is_valid_email('santa@joltem.com'))

    def test_invalid_email(self):
        self.assertFalse(is_valid_email('test@test.test'))