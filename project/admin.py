from django.contrib import admin
from django_markdown.admin import MarkdownModelAdmin

from . import models


admin.site.register(models.Equity)
admin.site.register(models.Impact)
admin.site.register(models.Project, MarkdownModelAdmin)
