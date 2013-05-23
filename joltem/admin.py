from django.contrib import admin
import project, task, solution

admin.site.register(project.models.Project)
admin.site.register(task.models.Task)
admin.site.register(solution.models.Solution)