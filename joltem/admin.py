""" Register Joltem models in Django admin. """

from django.contrib import admin
from django_markdown.admin import MarkdownModelAdmin

from .models import User, Vote, Comment, Notification


class UserAdmin(admin.ModelAdmin):
    list_display = 'username', 'date_joined', 'impact', 'is_active'


admin.site.register(Comment, MarkdownModelAdmin)
admin.site.register(Notification)
admin.site.register(User, UserAdmin)
admin.site.register(Vote)
