# coding: utf-8
from django import forms

from .models import Task


class TaskCreateForm(forms.ModelForm):

    priority = forms.ChoiceField(
        widget=forms.RadioSelect(),
        choices=Task.PRIORITY_CHOICES,
        initial=Task.NORMAL_PRIORITY,
    )

    class Meta:
        model = Task
        fields = ('title', 'description', 'priority', 'project', 'owner',)

    def clean_title(self):
        return self.cleaned_data.get('title', '').strip()


class TaskEditForm(forms.ModelForm):

    priority = forms.ChoiceField(
        widget=forms.RadioSelect(),
        choices=Task.PRIORITY_CHOICES,
    )

    class Meta:
        model = Task
        fields = ('title', 'description', 'priority',)

    def clean_title(self):
        return self.cleaned_data.get('title', '').strip()
