from django.contrib import admin
from joltem import models

admin.site.register(models.Project)
admin.site.register(models.Task)
admin.site.register(models.TaskBranch)