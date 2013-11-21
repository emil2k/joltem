""" Account views. """
from authomatic import Authomatic, adapters
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, REDIRECT_FIELD_NAME, login
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DeleteView

from .forms import SignUpForm, GeneralSettingsForm, SSHKeyForm
from joltem.views.generic import ValidUserMixin
from .models import User, OAuth


authomatic = Authomatic(
    settings.AUTHOMATIC, settings.SECRET_KEY, debug=settings.DEBUG,
    report_errors=not settings.DEBUG)


def authomatic_login(request, provider):
    """ OAuth login.

    :return HttpResponse:

    """

    redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, 'home')

    response = HttpResponse()

    result = authomatic.login(
        adapters.DjangoAdapter(request, response), provider)

    if not result:
        return response

    if result.error:
        messages.add_message(
            request, messages.ERROR,
            result.error.message or 'Unknow error. Please try another time.')

        return redirect('sign_in')

    if result.user:

        if not (result.user.name and result.user.id):
            result.user.update()

        try:
            user = User.objects.get(
                oauth__service=result.provider.name,
                oauth__service_id=result.user.id,
            )
            # Fuck django auth
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

            return redirect(redirect_to)

        except User.DoesNotExist:
            if request.user.is_authenticated():
                OAuth.objects.get_or_create(
                    service=result.provider.name,
                    service_id=result.user.id,
                    user=request.user,
                    username=result.user.username or request.user.name,
                )
                messages.add_message(
                    request, messages.INFO, 'Provider attached.')

                return redirect(redirect_to)

        first_name, _, last_name = result.user.name.partition(' ')
        request.session.setdefault('oauth', {})
        request.session['oauth'][result.provider.name] = dict(
            service_id=result.user.id,
            first_name=first_name,
            last_name=last_name,
            email=result.user.email,
            username=result.user.username or request.user.name,
        )

    return redirect('sign_up')


class ExtraContextMixin(object):

    """Accepts ``extra_context`` dict in ``django.contrib.auth`` way."""

    def get_context_data(self, **kwargs):
        """ Make template context.

        :return dict:

        """
        context = super(ExtraContextMixin, self).get_context_data(**kwargs)

        extra_context = self.kwargs.get('extra_context')
        if extra_context is not None:
            context.update(extra_context)

        return context


class SignUpView(ExtraContextMixin, CreateView):

    """Creates new user.

    In addition to creating new user it:

    - logs user in;
    - sets gravatar.

    """

    form_class = SignUpForm
    template_name = 'registration/sign_up.html'
    success_url = reverse_lazy('intro')

    @method_decorator(user_passes_test(
        test_func=lambda user: user.is_anonymous(),
        login_url=settings.LOGIN_REDIRECT_URL,
    ))
    def dispatch(self, *args, **kwargs):
        """ Check for user is anonimous.

        :return HttpResponse:

        """
        return super(SignUpView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """ Save user.

        :return HttpResponse:

        """
        response = super(SignUpView, self).form_valid(form)

        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1'],
        )
        login(self.request, user)

        if user.set_gravatar_email(form.cleaned_data['gravatar_email']):
            user.save()

        return response

    def get_form_kwargs(self):
        """ Setup form from attached OAuth providers.

        :return dict:

        """
        kwargs = super(SignUpView, self).get_form_kwargs()
        initial = kwargs['initial']
        for oauth in self.request.session.get('oauth', {}).values():
            initial.setdefault('username', oauth.get('username'))
            initial.setdefault('email', oauth.get('email'))
            initial.setdefault('first_name', oauth.get('first_name'))
            initial.setdefault('last_name', oauth.get('last_name'))
        return kwargs


class BaseAccountView(ValidUserMixin, ExtraContextMixin):

    """Provides ``login_required`` decorator and extra context acceptance. """

    pass


class GeneralSettingsView(BaseAccountView, UpdateView):

    """Updates user's general settings."""

    form_class = GeneralSettingsForm
    template_name = 'account/general_settings.html'
    success_url = reverse_lazy('account')

    def get_object(self):
        """ Return current user.

        :return User:

        """
        return self.request.user

    def form_valid(self, form):
        """ Save form.

        :return HttpResponse:

        """
        response = super(GeneralSettingsView, self).form_valid(form)

        user = form.instance
        if user.set_gravatar_email(form.cleaned_data['gravatar_email']):
            user.save()

        return response

    def get_context_data(self, **kwargs):
        """ Load information about connected OAuth.

        :return dict: Template's context

        """
        context = super(GeneralSettingsView, self).get_context_data(**kwargs)
        services = list(self.object.oauth_set.all())
        context['providers'] = [
            provider for provider in settings.AUTHOMATIC
            if not provider in [s.service for s in services]
        ]
        context['services'] = services
        return context


class SSHKeyCreateView(BaseAccountView, CreateView):

    """Adds public SSH key to account and shows available ones."""

    form_class = SSHKeyForm
    template_name = 'account/ssh_keys.html'

    def form_valid(self, form):
        """ Save form.

        :return HttpResponseRedirect:

        """
        ssh_key_instance = form.save(commit=False)
        ssh_key_instance.user = self.request.user
        ssh_key_instance.blob = form.cleaned_data['key']
        ssh_key_instance.save()

        return redirect('account_keys')

    def get_context_data(self, **kwargs):
        """ Make context.

        :return dict: a context

        """
        context = super(SSHKeyCreateView, self).get_context_data(**kwargs)

        context['ssh_key_list'] = self.request.user.authentication_set.all()

        return context


class SSHKeyDeleteView(BaseAccountView, DeleteView):

    """Deletes public SSH key by id from account."""

    template_name = 'account/ssh_key_confirm_delete.html'
    success_url = reverse_lazy('account_keys')

    def get_queryset(self):
        """ Get queryset.

        :return Queryset:

        """
        return self.request.user.authentication_set
