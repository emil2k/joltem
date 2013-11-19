""" Register Joltem models in Django admin. """

from django.contrib import admin

import project.models
import task.models
import solution.models

from .models import User, Vote, Comment

admin.site.register(Comment)
admin.site.register(User)
admin.site.register(Vote)
admin.site.register(project.models.Project)
admin.site.register(solution.models.Solution)
admin.site.register(task.models.Task)
