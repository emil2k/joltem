""" Register Joltem models in Django admin. """


from django.contrib import admin
from django.contrib.contenttypes.generic import GenericTabularInline
from django_markdown.admin import MarkdownModelAdmin

from .models import Solution
from joltem.models import Vote


class _VoteInlideAdmin(GenericTabularInline):
    ct_field = "voteable_type"
    ct_fk_field = "voteable_id"
    extra = 0
    model = Vote
    raw_id_fields = 'voter',


class _SolutionAdmin(MarkdownModelAdmin):

    list_display = 'default_title', 'is_completed', 'is_closed', 'is_archived'
    inlines = _VoteInlideAdmin,
    list_filter = 'project',
    list_select_related = True
    search_fields = 'title',

admin.site.register(Solution, _SolutionAdmin)
