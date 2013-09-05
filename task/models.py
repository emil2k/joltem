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
    owner = models.ForeignKey(User)
    project = models.ForeignKey('project.Project')
    parent = models.ForeignKey('solution.Solution', null=True, blank=True, related_name="subtask_set")
    author = models.ForeignKey(User, related_name="tasks_authored_set")  # user who created the task

    def __unicode__(self):
        return self.title

    @property
    def get_subtask_count(self):
        """
        Count of accepted subtasks stemming from this task
        """
        count = 0
        for solution in self.solution_set.filter(is_accepted=True):
            count += solution.get_subtask_count()
        return count

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
            if parent_solution \
                    and parent_solution.owner_id != self.author_id:
                if not parent_solution.is_closed and not parent_solution.is_completed:
                    return parent_solution.is_owner(user)
            elif parent_task \
                    and parent_task.owner_id != self.author_id:
                if not parent_task.is_closed and parent_task.is_accepted:
                    return parent_task.is_owner(user)
        return self.project.is_admin(user.id)  # default to project admin

    def get_notification_text(self, notification):
        from joltem.utils import list_string_join
        from joltem.models.comments import NOTIFICATION_TYPE_COMMENT_ADDED
        if NOTIFICATION_TYPE_COMMENT_ADDED == notification.type:
            first_names = self.get_commentator_first_names(
                queryset=self.comment_set.all().order_by("-time_commented"),
                exclude=[notification.user]
            )
            return "%s commented on task %s" % (list_string_join(first_names), self.title)
        return "Task updated : %s" % self.title

    def get_notification_url(self, url):
        from django.core.urlresolvers import reverse
        return reverse("project:task:task", args=[self.project.name, self.id])

