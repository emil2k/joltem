# coding: utf-8
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):

    first_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    gravatar_email = forms.EmailField(label='Gravatar', required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
