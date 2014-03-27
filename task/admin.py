from django.contrib import admin
from django_markdown.admin import MarkdownModelAdmin

from . import models


class TaskAdmin(MarkdownModelAdmin):
    list_display = 'title', 'project', 'owner'
    list_filter = 'project',
    list_select_related = True
    search_fields = 'title',

admin.site.register(models.Task, TaskAdmin)
