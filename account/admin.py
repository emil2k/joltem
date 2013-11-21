""" Register Joltem models in Django admin. """

from django.contrib import admin

from .models import OAuth


admin.site.register(OAuth)
