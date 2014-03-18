""" Register Joltem models in Django admin. """

from django.contrib import admin
from django_markdown.admin import MarkdownModelAdmin

import project.models
import task.models

from .models import User, Vote, Comment, Notification
from .models.utils import Tag, TaggedItem
from taggit.models import Tag as TaggitTag


class UserAdmin(admin.ModelAdmin):
    list_display = 'username', 'date_joined', 'impact', 'is_active'


admin.site.register(Comment, MarkdownModelAdmin)
admin.site.register(Notification)
admin.site.register(project.models.Equity)
admin.site.register(project.models.Impact)
admin.site.register(project.models.Project, MarkdownModelAdmin)
admin.site.register(task.models.Task, MarkdownModelAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Vote)
admin.site.register(Tag)
admin.site.unregister(TaggitTag)  # because using custom tag
admin.site.register(TaggedItem)
