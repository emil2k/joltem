# coding: utf-8
import binascii

from twisted.conch.ssh.keys import BadKeyError, Key as ConchKey
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _

from joltem.models import User
from git.models import Authentication


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

    def clean_username(self):
        """ Fix Django clean username method.

        :return str:

        """
        username = self.cleaned_data["username"]
        try:
            User._default_manager.get(username=username)
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

    first_name = forms.CharField(label=_('First name'), max_length=30)
    email = forms.EmailField(label=_('Email'))
    gravatar_email = forms.EmailField(label=_('Gravatar'), required=False)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')


class SSHKeyForm(forms.ModelForm):

    class Meta:
        model = Authentication
        fields = ('name', 'key',)

    error_messages = {
        'unknown_key': _('Cannot guess the type of given key.'),
        'must_be_rsa': _('SSH key has to be RSA.'),
        'must_be_public': _('SSH key has to be private.'),
    }

    def clean_key(self):
        """Validates SSH private key."""
        ssh_key_str = self.cleaned_data['key'].strip()

        try:
            ssh_key = ConchKey.fromString(ssh_key_str)
        except (BadKeyError, IndexError, binascii.Error):
            raise forms.ValidationError(self.error_messages['unknown_key'])

        if not ssh_key.sshType() == 'ssh-rsa':
            raise forms.ValidationError(self.error_messages['must_be_rsa'])

        if not ssh_key.isPublic():
            raise forms.ValidationError(self.error_messages['must_be_public'])

        return ssh_key_str
