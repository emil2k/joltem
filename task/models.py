""" Task's models.  """

from django.db import models
from django.utils import timezone
from django.core import serializers
from django.conf import settings
from django.core.cache import cache

from joltem.models import Commentable
from joltem.models.generic import Updatable


class Task(Commentable, Updatable):

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

    HIGH_PRIORITY = 2
    NORMAL_PRIORITY = 1
    LOW_PRIORITY = 0
    PRIORITY_CHOICES = (
        (HIGH_PRIORITY, 'high'),
        (NORMAL_PRIORITY, 'normal'),
        (LOW_PRIORITY, 'low'),
    )

    priority = models.PositiveSmallIntegerField(
        choices=PRIORITY_CHOICES,
        default=NORMAL_PRIORITY,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)

    is_reviewed = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)

    time_posted = models.DateTimeField(default=timezone.now)
    time_reviewed = models.DateTimeField(null=True, blank=True)
    time_closed = models.DateTimeField(null=True, blank=True)

    # Relations
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    project = models.ForeignKey('project.Project')
    parent = models.ForeignKey(
        'solution.Solution', null=True, blank=True, related_name="subtask_set")
    # user who created the task
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="tasks_authored_set")

    def __unicode__(self):
        return self.title

    @property
    def followers(self):
        """ Get users for notify.

        :returns: A set of users.

        """
        return set([
            self.author, self.owner] +
            list(self.iterate_commentators()) +
            [v.voter for v in self.vote_set.select_related('voter')])

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

    def save(self, **kwargs):
        """ Override to notify at creation. """

        created = not self.pk
        super(Task, self).save(**kwargs)
        if created:
            self.notify_created()

        # Clear tabs counter cache
        cache.delete('%s:tasks_tabs' % self.project_id)

    def put_vote(self, voter, is_accepted):
        """ Cast or overwrites a vote cast while reviewing a task.

        Keyword arguments :
        voter -- a model instance of the user casting the vote.
        is_accepted -- whether the voter accepts the task as ready.

        """
        vote, create = Vote.objects.get_or_create(
            voter=voter, task=self, defaults={
                'voter_impact': voter.impact
            })
        vote.voter_impact = voter.impact
        vote.is_accepted = is_accepted
        vote.time_voted = timezone.now()
        vote.save()

        ntype = settings.NOTIFICATION_TYPES.vote_added if create else settings.NOTIFICATION_TYPES.vote_updated # noqa
        for user in self.followers:
            if user == vote.voter:
                continue

            self.notify(user, ntype, create, kwargs={
                "voter_first_name": vote.voter.first_name,
                "type": "task",
                "title": self.title,
            })

        self.determine_acceptance(vote)

    def determine_acceptance(self, vote):
        """ Determine if the task's review is complete.

        Called after each vote is cast on a task to determine if the task's
        review is complete, and if so whether it was accepted or not.

        Criteria for acceptance :
        - An acceptance vote from a project admin or manager.

        Criteria for rejection :
        - A rejection vote from a project admin or manager.

        :param vote: the vote to process.

        """
        if self.project.is_admin(vote.voter_id) or \
                self.project.is_manager(vote.voter_id):
            self.mark_reviewed(vote.voter, vote.is_accepted)

    def mark_reviewed(self, acceptor, is_accepted):
        """ Indicate that the task has been reviewed.

        Change the `is_reviewed` state and set `is_accepted`.

        Keyword arguments :
        acceptor -- person who accepted the task, might become owner of task
        is_accepted -- whether the task was accepted or rejected

        """
        # a suggested task
        if is_accepted and \
                (not self.parent or self.parent.owner_id != self.author_id):
            self.owner = acceptor
        self.is_reviewed = True
        self.is_accepted = is_accepted
        self.time_reviewed = timezone.now()
        self.is_closed = False  # if task was closed, reopen it
        self.time_closed = None
        self.save()
        self.notify_reviewed(acceptor, is_accepted)

    def notify_reviewed(self, acceptor, is_accepted):
        """ Notify task author.

        If not the acceptor, that the task was either accepted or rejected.

        """
        ntype = settings.NOTIFICATION_TYPES.task_accepted if is_accepted\
            else settings.NOTIFICATION_TYPES.task_rejected

        listeners = self.followers - set([acceptor])
        for user in listeners:
            self.notify(user, ntype, True)

    def notify_created(self):
        """ Send out appropriate notifications about the task being posted. """
        if self.parent:
            if self.parent.owner_id != self.author_id:
                self.notify(
                    self.parent.owner, settings.NOTIFICATION_TYPES.task_posted,
                    True, kwargs={"role": "parent_solution"})
        else:
            for admin in self.project.admin_set.all():
                if admin.id != self.author_id:
                    self.notify(
                        admin, settings.NOTIFICATION_TYPES.task_posted, True,
                        kwargs={"role": "project_admin"})

    def default_title(self):
        """ Just prevent conflict with solutions.

        :return str:

        """
        return self.title

    def get_notification_url(self, url):
        """ Get notification URL.

        :return str:

        """
        from django.core.urlresolvers import reverse
        return reverse("project:task:task", args=[self.project.id, self.id])

    def get_notification_kwargs(self, notification=None, **kwargs):
        """ Precache notification kwargs.

        :returns: Kwargs dictionary

        """
        python_serializer = serializers.python.Serializer()
        kwargs = super(Task, self).get_notification_kwargs(
            notification, **kwargs)
        kwargs['owner'] = python_serializer.serialize(
            [self.owner], fields=('username', 'first_name'))[0]
        kwargs['author'] = python_serializer.serialize(
            [self.author], fields=('username', 'first_name'))[0]
        return kwargs


class Vote(models.Model):

    """ A simply yay or nay vote on a task that is being reviewed.

    Attributes :
    voter_impact -- the impact at the time of the vote
    is_accepted -- whether the vote indicated and acceptance
        ( or rejection ) of the task. default false.
    time_voted -- the time voted
    voter -- the user who voted
    task -- the task voted on

    """

    voter_impact = models.BigIntegerField()
    is_accepted = models.BooleanField(default=False)
    time_voted = models.DateTimeField(default=timezone.now)
    # Relations
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="task_vote_set")
    task = models.ForeignKey(Task)

    class Meta:
        unique_together = ['voter', 'task']
