""" Project's forms. """


from django import forms
from django.core.exceptions import ValidationError

from .models import Project

class ProjectCreateForm(forms.ModelForm):

    """ Form for creating new project.

    :param ownership:

    """

    ownership = forms.IntegerField()

    class Meta:
        model = Project
        fields = ('title', 'description', 'exchange_periodicity',
                  'exchange_magnitude')

    def clean_title(self):
        """ Clean up title, trim whitespace.

        :return str:

        """
        return self.cleaned_data.get('title', '').strip()

    def clean_ownership(self):
        """ Enforce limits on ownership stake.

        :return int: 0-100 integer representing initial ownership of user
            creating the project.

        """
        own = int(self.cleaned_data.get('ownership', 0))
        if own < 0:
            raise ValidationError("You can't own less than 0%.",
                                  code='invalid')
        elif own > 100:
            raise ValidationError("You can't own more than 100%.",
                                  code='invalid')
        return own

    def clean_exchange_periodicity(self):
        """ Enforce limits on exchange event periodicity.

        Minimum should be 1 month and the maximum should be 12 months.

        :return int: 1-12 integer, representing number of months between
            exchange events.

        """
        p = int(self.cleaned_data.get('exchange_periodicity', 0))
        if p < 1:
            raise ValidationError("Invalid exchange period.",
                                  code='invalid')
        elif p > 12:
            raise ValidationError(
                "Maximum time between exchange events is 12 months.",
                code='invalid')
        return p

    def clean_exchange_magnitude(self):
        """ Enforce limits on exchange magnitude stake.

        :return int: 0-100 integer representing % of impact that can
            be exchanged at each exchange event.

        """
        m = int(self.cleaned_data.get('exchange_magnitude', 0))
        if m < 0:
            raise ValidationError(
                "You can't exchange less than 0% each time.", code='invalid')
        elif m > 100:
            raise ValidationError(
                "You can't exchange more than 100% each time.", code='invalid')
        return m


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
