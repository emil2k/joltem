""" Forms for core app. """

from django.forms import forms, fields, widgets
from joltem.forms.utils import validate_username, validate_username_available

class UsernameField(fields.CharField):

    default_validators = [validate_username, validate_username_available]

    def clean(self, value):
        value = self.to_python(value).strip()
        return super(UsernameField, self).clean(value)

class SignUpForm(forms.Form):

    """ Form for processing a sign up. """

    # todo add invite code hidden field, and invite code validator
    username = UsernameField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    first_name = fields.CharField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = fields.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = fields.EmailField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Email'}))
    gravatar = fields.EmailField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Gravatar Email'}))
    password = fields.CharField(
        min_length=8,
        max_length=30,
        required=True,
        widget=widgets.PasswordInput(attrs={'placeholder': 'Password'}))
    password_confirm = fields.CharField(
        min_length=8,
        max_length=30,
        required=True,
        widget=widgets.PasswordInput(attrs={'placeholder': 'Confirm Password'}))

    def clean(self):
        """ Validate password confirmation.

        :return: cleaned data dict.

        """
        # todo add test for this
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords don't match.")
        return self.cleaned_data

