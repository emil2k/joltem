""" Test forms used in the project app. """
from django.core.exceptions import ValidationError

from django.test import TestCase

from ..forms import ProjectCreateForm

class ProjectCreateFormTest(TestCase):

    """ Test ProjectCreateForm. """

    def setUp(self):
        self.form = ProjectCreateForm()
        self.form.cleaned_data = {}

    def test_ownership_minimum(self):
        """ Test ownership minimum. """
        self.form.cleaned_data['ownership'] = -1
        with self.assertRaises(ValidationError):
            self.form.clean_ownership()

    def test_ownership_maximum(self):
        """ Test ownership maximum. """
        self.form.cleaned_data['ownership'] = 101
        with self.assertRaises(ValidationError):
            self.form.clean_ownership()
