""" Task's models.  """

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from joltem.models import Commentable

NOTIFICATION_TYPE_TASK_POSTED = "task_posted"
NOTIFICATION_TYPE_TASK_ACCEPTED = "task_accepted"
NOTIFICATION_TYPE_TASK_REJECTED = "task_rejected"


class Task(Commentable):

    """ A task is a description of work.

    The `owner` of the task is responsible for the administrating and merging
    of the work as necessary. The `author` is the person who originally wrote
    up the task.

    After creation a task must be curated through a staging process, if
    accepted the task is opened and it is available for people to post
    solutions until it is closed by the owner.

    Attributes :
    title -- title of task.
    description -- description of task, formatted with markdown.
    is_reviewed -- whether or not the task has been reviewed, if it hasn't
        then it is being reviewed. default False.
    is_accepted -- if the task has been reviewed, whether or not it was
        accepted or rejected. default False.
    is_closed -- if the task was reviewed and accepted, whether or not it is
        closed to new solutions. if a task is closed otherwise it means it is
        deprecated. default False.
    time_posted -- date and time when the task was originally posted.
    time_reviewed -- date and time of when the review of the task was completed
    time_closed -- date and time of last time (could be reopened) when the task
        was marked closed.
    owner -- the user responsible for administrating the task.
    project -- the project the task belongs to.
    parent -- if task is a subtask to a solution, this is the parent solution.
    author -- the person who initially suggested the task.

    """

    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    is_reviewed = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    time_posted = models.DateTimeField(default=timezone.now)
    time_reviewed = models.DateTimeField(null=True, blank=True)
    time_closed = models.DateTimeField(null=True, blank=True)
    # Relations
    owner = models.ForeignKey(User)
    project = models.ForeignKey('project.Project')
    parent = models.ForeignKey(
        'solution.Solution', null=True, blank=True, related_name="subtask_set")
    author = models.ForeignKey(
        User, related_name="tasks_authored_set")  # user who created the task

    def __unicode__(self):
        return self.title

    def get_subtask_count(
            self, solution_is_completed=False, solution_is_closed=False,
            task_is_reviewed=False, task_is_accepted=False,
            task_is_closed=False):
        """ Count of tasks stemming from this task, that meet state criteria.

        Keyword arguments :
        solution_is_completed -- whether solutions included in the count should
            be completed.
        solution_is_closed -- whether solutions included in the count should
            be closed.
        task_is_reviewed -- whether tasks included in the count should
            be reviewed.
        task_is_accepted -- whether tasks included in the count should
            be accepted.
        task_is_closed -- whether tasks included in the count should be closed.

        :return int: Count

        """
        count = 0
        for solution in self.solution_set.filter(
                is_completed=solution_is_completed,
                is_closed=solution_is_closed):
            count += solution.get_subtask_count(
                solution_is_completed, solution_is_closed,
                task_is_reviewed, task_is_accepted, task_is_closed
            )
        return count

    def iterate_parents(self):
        """ Iterate through parents.

        Returns a tuple with the parent solution and task.

        """
        parent_solution, parent_task = self.parent, None
        yield parent_solution, parent_task
        while parent_solution or parent_task:
            if parent_solution:
                parent_solution, parent_task = (
                    parent_solution.solution, parent_solution.task)
            elif parent_task:
                parent_solution, parent_task = parent_task.parent, None
            if parent_solution or parent_task:
                yield parent_solution, parent_task

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """ Override to notify at creation. """

        created = not self.pk
        super(Task, self).save(
            force_insert, force_update, using, update_fields)
        if created:
            self.notify_created()

    def put_vote(self, voter, is_accepted):
        """ Casts or overwrites a vote cast while reviewing a task.

        Keyword arguments :
        voter -- a model instance of the user casting the vote.
        is_accepted -- whether the voter accepts the task as ready.

        """
        try:
            vote = Vote.objects.all().get(voter=voter, task=self)
        except Vote.DoesNotExist:
            vote = Vote(
                task=self,
                voter=voter
            )
        vote.voter_impact = voter.get_profile().impact
        vote.is_accepted = is_accepted
        vote.time_voted = timezone.now()
        vote.save()
        self.determine_acceptance(vote)

    def determine_acceptance(self, vote):
        """
        Called after each vote is cast on a task to determine if the task's review is complete, and if so
        whether it was accepted or not.

        Criteria for acceptance :
        - An acceptance vote from a project admin.

        Criteria for rejection :
        - A rejection vote from a project admin.

        Keyword argument :
        vote -- the vote to process.

        """
        if self.project.is_admin(vote.voter_id):
            self.mark_reviewed(vote.voter, vote.is_accepted)

    def mark_reviewed(self, acceptor, is_accepted):
        """
        Indicate that the task has been reviewed, change the `is_reviewed` state and set `is_accepted`.

        Keyword arguments :
        acceptor -- person who accepted the task, might become owner of task
        is_accepted -- whether the task was accepted or rejected

        """
        if is_accepted and \
                (not self.parent or self.parent.owner_id != self.author_id):  # a suggested task
                self.owner = acceptor
        self.is_reviewed = True
        self.is_accepted = is_accepted
        self.time_reviewed = timezone.now()
        self.is_closed = False  # if task was closed, reopen it
        self.time_closed = None
        self.save()
        self.notify_reviewed(acceptor, is_accepted)

    def notify_reviewed(self, acceptor, is_accepted):
        """
        Notify task author, if not the acceptor, that the task was either accepted or rejected.

        """
        type = NOTIFICATION_TYPE_TASK_ACCEPTED if is_accepted else NOTIFICATION_TYPE_TASK_REJECTED
        if self.owner_id != self.author_id:  # suggested task accepted
            self.notify(self.author, type, True)
        elif acceptor.id != self.author_id:
            self.notify(self.author, type, True)

    def notify_created(self):
        """Send out appropriate notifications about the task being posted"""
        if self.parent:
            if self.parent.owner_id != self.author_id:
                self.notify(self.parent.owner, NOTIFICATION_TYPE_TASK_POSTED, True, kwargs={
                            "role": "parent_solution"})
        else:
            for admin in self.project.admin_set.all():
                if admin.id != self.author_id:
                    self.notify(admin, NOTIFICATION_TYPE_TASK_POSTED, True, kwargs={
                                "role": "project_admin"})

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
                return "%s posted a task on your solution \"%s\"" % (self.author.first_name, self.parent.default_title)
            elif notification.kwargs["role"] == "project_admin":
                return "%s posted a task" % self.author.first_name
        elif NOTIFICATION_TYPE_TASK_ACCEPTED == notification.type:
            return "Your task \"%s\" was accepted" % self.title
        elif NOTIFICATION_TYPE_TASK_REJECTED == notification.type:
            return "Your task \"%s\" was not accepted" % self.title
        return "Task updated : %s" % self.title

    def get_notification_url(self, url):
        from django.core.urlresolvers import reverse
        return reverse("project:task:task", args=[self.project.name, self.id])


class Vote(models.Model):
    """
    A simply yay or nay vote on a task that is being reviewed.

    Attributes :
    voter_impact -- the impact at the time of the vote
    is_accepted -- whether the vote indicated and acceptance ( or rejection ) of the task. default false.
    time_voted -- the time voted
    voter -- the user who voted
    task -- the task voted on

    """
    voter_impact = models.BigIntegerField()
    is_accepted = models.BooleanField(default=False)
    time_voted = models.DateTimeField(default=timezone.now)
    # Relations
    voter = models.ForeignKey(User, related_name="task_vote_set")
    task = models.ForeignKey(Task)

    class Meta:
        unique_together = ['voter', 'task']
