""" Supports Git models im Django admin. """


from django.contrib import admin
from git import models

admin.site.register(models.Repository)
admin.site.register(models.Authentication)
