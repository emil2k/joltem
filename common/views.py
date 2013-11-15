# coding: utf-8
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class ValidUserMixin(object):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ValidUserMixin, self).dispatch(request, *args, **kwargs)
