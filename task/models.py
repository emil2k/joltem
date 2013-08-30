from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from joltem.models import Commentable


class Task(Commentable):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    is_accepted = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    time_posted = models.DateTimeField(default=timezone.now)
    time_accepted = models.DateTimeField(null=True, blank=True)
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
            count += solution.get_subtask_count
        return count

    def is_owner(self, user):
        """
        Whether the passed user is person who posted the task
        """
        return self.owner_id == user.id

    def is_acceptor(self, user):
        """
        Whether passed user is the person responsible for accepting the task
        """
        # todo make function
        if self.parent:
            if self.parent.task:
                if self.parent.task.is_closed or not self.parent.task.is_accepted:
                    return self.parent.task.is_acceptor(user)  # fallback to acceptor
                else:
                    return self.parent.task.is_owner(user)  # owner available
            elif self.parent.solution:
                # todo
                pass
        return self.project.is_admin(user.id)  # default to project admin