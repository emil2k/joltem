from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from joltem.models import Commentable


class Task(Commentable):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    time_posted = models.DateTimeField(default=timezone.now)
    time_closed = models.DateTimeField(null=True, blank=True)
    # Relations
    project = models.ForeignKey('project.Project')
    parent = models.ForeignKey('solution.Solution', null=True, blank=True, related_name="subtask_set")
    owner = models.ForeignKey(User)

    def __unicode__(self):
        return self.title

    @property
    def get_subtask_count(self):
        """
        Count of subtasks stemming from this task
        """
        count = 0
        for solution in self.solution_set.all():
            count += solution.get_sub
        return count

    def is_owner(self, user):
        """
        Whether the passed user is person who posted the task
        """
        return self.owner_id == user.id