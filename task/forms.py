""" Tasks forms. """

from django import forms

from .models import Task


class TaskCreateForm(forms.ModelForm):

    """ Implement tasks creation. """

    priority = forms.ChoiceField(
        widget=forms.RadioSelect(),
        choices=Task.PRIORITY_CHOICES,
        initial=Task.NORMAL_PRIORITY,
    )

    class Meta:
        model = Task
        fields = ('title', 'description', 'priority', 'project', 'owner',
                  'tags')

    def clean_title(self):
        """ Strip whitespaces from title.

        :return str:

        """
        return self.cleaned_data.get('title', '').strip()


class TaskEditForm(forms.ModelForm):

    """ Implement tasks edition. """

    priority = forms.ChoiceField(
        widget=forms.RadioSelect(),
        choices=Task.PRIORITY_CHOICES,
    )

    class Meta:
        model = Task
        fields = ('title', 'description', 'priority', 'tags')

    def clean_title(self):
        """ Strip whitespaces from title.

        :return str:

        """
        return self.cleaned_data.get('title', '').strip()
