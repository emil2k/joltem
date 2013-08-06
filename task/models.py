from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from project.models import Project


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    time_posted = models.DateTimeField(default=timezone.now)
    time_closed = models.DateTimeField(null=True, blank=True)
    # Relations
    project = models.ForeignKey(Project)
    parent = models.ForeignKey('solution.Solution', null=True, blank=True, related_name="tasks") # TODO rename related to subtask_set
    owner = models.ForeignKey(User)

    def __unicode__(self):
        return self.title

    @property
    def subtasks(self):  # TODO rename to subtask_count, and probably need to move this to a manager
        """
        Count of open subtasks stemming from this task
        """
        count = 0
        for solution in self.solution_set.all():
            count += solution.subtask_set
        return count

    def is_owner(self, user):
        """
        Whether the passed user is person who posted the task
        """
        return self.owner_id == user.id