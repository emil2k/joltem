from django.contrib import admin

from .models import GitReceivePackEvent, GitReport, GitUploadPackEvent

admin.site.register(GitReport)
admin.site.register(GitReceivePackEvent)
admin.site.register(GitUploadPackEvent)
