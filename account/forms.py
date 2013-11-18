# coding: utf-8

""" Account forms. """

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _

from joltem.models import User


class SignUpForm(UserCreationForm):

    """ Exported classes should have docstrings. """

    username = forms.RegexField(
        label=_('Username'),
        max_length=30,
        regex=r'^[0-9A-Za-z]+$',
        error_messages={
            'invalid': _('This value may contain only letters and numbers.'),
        },
    )
    first_name = forms.CharField(label=_('First name'), max_length=30)
    email = forms.EmailField(label=_('Email'))
    gravatar_email = forms.EmailField(label=_('Gravatar'), required=False)

    def clean_username(self):
        """ Fix Django clean username method.

        :return str:

        """
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class GeneralSettingsForm(forms.ModelForm):

    """ Exported classes should have docstrings. """

    first_name = forms.CharField(label=_('First name'), max_length=30)
    email = forms.EmailField(label=_('Email'))
    gravatar_email = forms.EmailField(label=_('Gravatar'), required=False)
    notify_by_email = forms.ChoiceField(choices=User.NOTIFY_CHOICES)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'notify_by_email')
