""" Repositories forms. """

from django import forms
from django.core.exceptions import ValidationError
from git.models import Repository


class RepositoryCreateForm(forms.ModelForm):

    """ Form for creating repositories. """

    class Meta:
        model = Repository
        fields = ('name', 'description')

    def clean_name(self):
        """ Clean up name of repository, trim whitespace.

        :return str: cleaned up name.

        """
        return self.cleaned_data.get('name', '').strip()

    def clean_description(self):
        """ Clean up description of repository, trim whitespace.

        :return str: cleaned up description.

        """
        return self.cleaned_data.get('description', '').strip()


class RepositoryActionForm(forms.Form):

    """ Form for initiating action on single repository.

    For example can be used to hide/unhide a repository.

    """

    repository_id = forms.IntegerField()

    def clean_repository_id(self):
        """ Check that repository matches a repository. """
        repository_id = int(self.cleaned_data.get('repository_id'))
        try:
            self.repository = Repository.objects.get(id=repository_id)
        except Repository.DoesNotExist:
            raise ValidationError("Repository does not exist.")
        return repository_id
