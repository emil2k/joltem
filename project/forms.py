""" Project's forms. """


from django import forms

from .models import Project


class ProjectSettingsForm(forms.ModelForm):

    """ Work with project's settings."""

    class Meta:
        model = Project
        fields = ('title', 'description', 'admin_set', 'manager_set',
                  'developer_set')

    def clean_title(self):
        """ Strip whitespaces.

        :return str:

        """
        return self.cleaned_data.get('title', '').strip()


class ProjectSubscribeForm(forms.Form):

    """ Check user's action. """

    subscribe = forms.Field(required=False)

    def clean_subscribe(self):
        """ Check subscribe in request.

        :return bool:

        """
        return bool(self.data.get('subscribe'))
