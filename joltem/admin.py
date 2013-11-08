from django.contrib import admin

import project.models
import task.models
import solution.models

admin.site.register(project.models.Project)
admin.site.register(task.models.Task)
admin.site.register(solution.models.Solution)
