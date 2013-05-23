from django.db import models
from project.models import Project


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    project = models.ForeignKey(Project)
    parent = models.ForeignKey('solution.Solution', null=True, blank=True, related_name="tasks")

    def __unicode__(self):
        return self.title