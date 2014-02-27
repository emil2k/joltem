""" Register Joltem models in Django admin. """

from django.contrib import admin

import project.models
import task.models

from .models import User, Vote, Comment, Notification


class UserAdmin(admin.ModelAdmin):
    list_display = 'username', 'date_joined', 'impact', 'is_active'


admin.site.register(Comment)
admin.site.register(Notification)
admin.site.register(project.models.Equity)
admin.site.register(project.models.Impact)
admin.site.register(project.models.Project)
admin.site.register(task.models.Task)
admin.site.register(User, UserAdmin)
admin.site.register(Vote)
