# coding: utf-8
from django.views.generic import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test

from common.views import ValidUserMixin
from .forms import SignUpForm, GeneralSettingsForm, SSHKeyForm


class SignUpView(CreateView):
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
        return super(SignUpView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        response = super(SignUpView, self).form_valid(form)

        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password1'],
        )
        login(self.request, user)

        if user.set_gravatar_email(form.cleaned_data['gravatar_email']):
            user.save()

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
        if user.set_gravatar_email(form.cleaned_data['gravatar_email']):
            user.save()

        return response

    def get_context_data(self, **kwargs):
        context = super(GeneralSettingsView, self).get_context_data(**kwargs)

        extra_context = self.kwargs.get('extra_context')
        if extra_context is not None:
            context.update(extra_context)

        return context


class SSHKeyCreateView(ValidUserMixin, CreateView):
    """Adds public SSH key to account and shows available ones."""

    form_class = SSHKeyForm
    template_name = 'account/ssh_keys.html'

    def form_valid(self, form):
        ssh_key_instance = form.save(commit=False)
        ssh_key_instance.user = self.request.user
        ssh_key_instance.blob = form.cleaned_data['key']
        ssh_key_instance.save()

        return redirect('account_keys')

    def get_context_data(self, **kwargs):
        context = super(SSHKeyCreateView, self).get_context_data(**kwargs)

        extra_context = self.kwargs.get('extra_context')
        if extra_context is not None:
            context.update(extra_context)
        context['ssh_key_list'] = self.request.user.authentication_set.all()

        return context


class SSHKeyDeleteView(ValidUserMixin, DeleteView):
    """Deletes public SSH key by id from account."""

    template_name = 'account/ssh_key_confirm_delete.html'
    success_url = reverse_lazy('account_keys')

    def get_queryset(self):
        return self.request.user.authentication_set

    def get_context_data(self, **kwargs):
        context = super(SSHKeyDeleteView, self).get_context_data(**kwargs)

        extra_context = self.kwargs.get('extra_context')
        if extra_context is not None:
            context.update(extra_context)

        return context
