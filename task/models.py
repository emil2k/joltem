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

    def iterate_parents(self):
        """
        Iterate through parents, returns a tuple with the parent solution and task
        """
        parent_solution, parent_task = self.parent, None
        yield parent_solution, parent_task
        while parent_solution or parent_task:
            if parent_solution:
                parent_solution, parent_task = parent_solution.solution, parent_solution.task
            elif parent_task:
                parent_solution, parent_task = parent_task.parent, None
            if parent_solution or parent_task:
                yield parent_solution, parent_task

    def is_acceptor(self, user):
        """
        Whether passed user is the person responsible for accepting the task
        """
        for parent_solution, parent_task in self.iterate_parents():
            if parent_task:
                if not parent_task.is_closed and parent_task.is_accepted:
                    return parent_task.is_owner(user)
            elif parent_solution:
                if not parent_solution.is_closed and not parent_solution.is_completed:
                    return parent_solution.is_owner(user)
        return self.project.is_admin(user.id)  # default to project admin