# coding: utf-8
from django.views.generic.edit import CreateView, UpdateView
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test

from common.views import ValidUserMixin
from .forms import SignUpForm, GeneralSettingsForm


class SignUpView(CreateView):
    """Creates new user.

    In addition to creating new user it:

    - logs user in;
    - creates profile.

    """

    form_class = SignUpForm
    template_name = 'registration/sign_up.html'
    success_url = reverse_lazy('intro')

    @method_decorator(user_passes_test(
        test_func=lambda user: user.is_anonymous(),
        login_url=settings.LOGIN_REDIRECT_URL,
    ))
    def dispatch(self, *args, **kwargs):
        return super(SignUpView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        response = super(SignUpView, self).form_valid(form)

        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1'],
        )
        login(self.request, user)

        # Setup profile.
        profile = user.get_profile()
        if profile.set_gravatar_email(form.cleaned_data['gravatar_email']):
            profile.save()

        return response

    def get_context_data(self, **kwargs):
        context = super(SignUpView, self).get_context_data(**kwargs)

        extra_context = self.kwargs.get('extra_context')
        if extra_context is not None:
            context.update(extra_context)

        return context


class GeneralSettingsView(ValidUserMixin, UpdateView):
    """Updates user's general settings."""

    form_class = GeneralSettingsForm
    template_name = 'account/general_settings.html'
    success_url = reverse_lazy('account')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        response = super(GeneralSettingsView, self).form_valid(form)

        user = form.instance
        profile = user.get_profile()
        if profile.set_gravatar_email(form.cleaned_data['gravatar_email']):
            profile.save()

        return response

    def get_context_data(self, **kwargs):
        context = super(GeneralSettingsView, self).get_context_data(**kwargs)

        extra_context = self.kwargs.get('extra_context')
        if extra_context is not None:
            context.update(extra_context)

        return context
