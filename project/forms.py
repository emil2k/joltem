""" Project's forms. """


from django import forms
from django.core.exceptions import ValidationError

from .models import Project
from joltem.forms import validate_username


class ProjectCreateForm(forms.ModelForm):

    """ Form for creating new project.

    :param ownership:

    """

    ownership = forms.IntegerField()
    agree = forms.BooleanField(required=False)
    exchange_periodicity = forms.IntegerField(initial=None)
    exchange_magnitude = forms.IntegerField(initial=None)
    is_private = forms.TypedChoiceField(
        coerce=lambda x: bool(int(x)), choices=((0, 'False'), (1, 'True')),
        widget=forms.RadioSelect)

    class Meta:
        model = Project
        fields = ('title', 'description', 'exchange_periodicity',
                  'exchange_magnitude')

    def clean_title(self):
        """ Clean up title, trim whitespace.

        :return str:

        """
        return self.cleaned_data.get('title', '').strip()

    def clean_agree(self):
        """ Enforce understanding agreement.

        :return bool: whether user understood and agreed to project creation.

        """
        if bool(self.cleaned_data.get('agree')):
            return True
        else:
            raise ValidationError(
                "You should check that you understand.", code='invalid')

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

    is_private = forms.TypedChoiceField(
        choices=((False, 'False'), (True, 'True')),
        widget=forms.RadioSelect)

    class Meta:
        model = Project
        fields = ('title', 'description', 'is_private')

    def clean_title(self):
        """ Strip whitespaces.

        :return str:

        """
        return self.cleaned_data.get('title', '').strip()


class ProjectGroupForm(forms.Form):

    """ Form for adding or removing a user from a project's group.

    :param username: username of referenced user.

    """

    username = forms.CharField(required=True, validators=[validate_username])


class ProjectSubscribeForm(forms.Form):

    """ Check user's action. """

    subscribe = forms.Field(required=False)

    def clean_subscribe(self):
        """ Check subscribe in request.

        :return bool:

        """
        return bool(self.data.get('subscribe'))
