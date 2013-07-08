from django.db import models
from django.contrib.auth.models import User
from project.models import Project

from datetime import datetime


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    time_posted = models.DateTimeField(default=datetime.now)
    # Relations
    project = models.ForeignKey(Project)
    parent = models.ForeignKey('solution.Solution', null=True, blank=True, related_name="tasks")
    owner = models.ForeignKey(User)

    def __unicode__(self):
        return self.title

    @property
    def subtasks(self):
        """
        Count of all subtasks stemming from this task
        """
        count = 0
        for solution in self.solution_set.all():
            count += solution.subtasks
        return count

    def is_owner(self, user):
        """
        Whether the passed user is person who posted the task
        """
        return self.owner_id == user.id