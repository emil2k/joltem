# coding: utf-8
from django.views.generic.edit import CreateView
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test

from .forms import SignUpForm


class SignUpView(CreateView):

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
        """Creates new user.

        In addition to creating new user it:

        - logs user in;
        - creates profile.

        """
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
