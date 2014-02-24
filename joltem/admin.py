""" Register Joltem models in Django admin. """

from django.contrib import admin

import project.models
import task.models
import gateway.models

from .models import User, Vote, Comment, Notification

admin.site.register(Comment)
admin.site.register(User)
admin.site.register(Vote)
admin.site.register(Notification)
admin.site.register(project.models.Project)
admin.site.register(project.models.Equity)
admin.site.register(project.models.Impact)
admin.site.register(gateway.models.GitReceivePackEvent)
admin.site.register(gateway.models.GitUploadPackEvent)
admin.site.register(task.models.Task)
