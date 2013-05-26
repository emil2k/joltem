from django.db import models
from django.contrib.auth.models import User
from project.models import Project


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    project = models.ForeignKey(Project)
    parent = models.ForeignKey('solution.Solution', null=True, blank=True, related_name="tasks")
    owner = models.ForeignKey(User)

    def __unicode__(self):
        return self.title

    def is_owner(self, user):
        """
        Whether the passed user is person who posted the task
        """
        return self.owner_id == user.id