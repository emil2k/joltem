""" Register Joltem models in Django admin. """


from django.contrib import admin

from .models import Solution


class _SolutionAdmin(admin.ModelAdmin):

    list_display = 'default_title', 'is_completed', 'is_closed'

admin.site.register(Solution, _SolutionAdmin)
