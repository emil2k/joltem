from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from joltem.models import Commentable

NOTIFICATION_TYPE_TASK_POSTED = "task_posted"
NOTIFICATION_TYPE_TASK_ACCEPTED = "task_accepted"

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

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Override to notify at creation
        """
        created = not self.pk
        super(Task, self).save(force_insert, force_update, using, update_fields)
        if created:
            self.notify_created()

    def mark_accepted(self, acceptor):
        """
        Mark task accepted, allow it to solicit solutions
        `owner`, specifies task owner responsible for administrating it if the task is a suggested task
        """
        if not self.parent or self.parent.owner_id != self.author_id:  # a suggested task, on master all considered suggested
            self.owner = acceptor
        else:
            self.owner = self.author
        self.is_accepted = True
        self.time_accepted = timezone.now()
        self.is_closed = False  # if task was closed, reopen it
        self.time_closed = None
        self.save()
        self.notify_accepted(acceptor)

    def mark_unaccepted(self):
        """
        Mark task unaccepted, disallow it to solicit solutions
        """
        self.owner = self.author  # revert ownership back to author when unaccepted
        self.is_accepted = False
        self.time_accepted = None
        self.save()
        self.notify_unaccepted()

    def notify_accepted(self, acceptor):
        """
        Notify task author, if not the owner, that the task was accepted
        """
        if self.owner_id != self.author_id:  # suggested task accepted
            self.notify(self.author, NOTIFICATION_TYPE_TASK_ACCEPTED, True)
        elif acceptor.id != self.author_id:
            self.notify(self.author, NOTIFICATION_TYPE_TASK_ACCEPTED, True)

    def notify_unaccepted(self):
        """
        Delete any notifications that the task was accepted
        """
        self.delete_notifications(self.author, NOTIFICATION_TYPE_TASK_ACCEPTED)

    def notify_created(self):
        """Send out appropriate notifications about the task being posted"""
        if self.parent:
            if self.parent.owner_id != self.author_id:
                self.notify(self.parent.owner, NOTIFICATION_TYPE_TASK_POSTED, True, kwargs={"role": "parent_solution"})
        else:
            for admin in self.project.admin_set.all():
                if admin.id != self.author_id:
                    self.notify(admin, NOTIFICATION_TYPE_TASK_POSTED, True, kwargs={"role": "project_admin"})

    def get_notification_text(self, notification):
        from joltem.utils import list_string_join
        from joltem.models.comments import NOTIFICATION_TYPE_COMMENT_ADDED
        if NOTIFICATION_TYPE_COMMENT_ADDED == notification.type:
            first_names = self.get_commentator_first_names(
                queryset=self.comment_set.all().order_by("-time_commented"),
                exclude=[notification.user]
            )
            return "%s commented on task \"%s\"" % (list_string_join(first_names), self.title)
        elif NOTIFICATION_TYPE_TASK_POSTED == notification.type:
            if notification.kwargs["role"] == "parent_solution":
                return "%s posted a task on your solution \"%s\"" % (self.owner.first_name, self.parent.default_title)
            elif notification.kwargs["role"] == "project_admin":
                return "%s posted a task" % self.owner.first_name
        elif NOTIFICATION_TYPE_TASK_ACCEPTED == notification.type:
            return "Your task \"%s\" was accepted" % self.title
        return "Task updated : %s" % self.title

    def get_notification_url(self, url):
        from django.core.urlresolvers import reverse
        return reverse("project:task:task", args=[self.project.name, self.id])

