# coding: utf-8
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class SignUpForm(UserCreationForm):

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

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class GeneralSettingsForm(forms.ModelForm):

    first_name = forms.CharField(label=_('First name'), max_length=30)
    email = forms.EmailField(label=_('Email'))
    gravatar_email = forms.EmailField(label=_('Gravatar'), required=False)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
