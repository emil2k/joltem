from django.db import models
from project.models import Project


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    parent = models.ForeignKey('self', null=True, blank=True)
    project = models.ForeignKey(Project)

    def __unicode__(self):
        return self.title