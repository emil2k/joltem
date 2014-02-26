""" Solution related models. """
import logging
from django.conf import settings
from django.core import serializers
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from model_utils.managers import PassThroughManager

from .managers import SolutionQuerySet
from joltem.models import Voteable, Commentable
from joltem.models.generic import Updatable


logger = logging.getLogger('joltem')


class Solution(Voteable, Commentable, Updatable):

    """
    A solution is an execution of work.

    States :
    is_completed -- whether or not the solution has been marked
        completed by its owner, when a solution is completed it is
        placed into peer review.
    is_closed -- indicates that work on the solution has ceased,
        without a completion, solution may be deprecated, inactive,
        etc.
    is_archived -- indicates the solution cannot be edited anymore,
        meaning it is closed for voting and commenting.

    """

    model_name = "solution"

    # Optional custom title to solution
    title = models.TextField(null=True, blank=True)
    # Description of solution for all involved
    description = models.TextField(null=True, blank=True)
    # Whether solution was marked completed
    is_completed = models.BooleanField(default=False)
    # Alternative to deletion of solution, to keep all relationships intact
    is_closed = models.BooleanField(default=False)
    # Whether solution was marked archived
    is_archived = models.BooleanField(default=False)

    # NOTE : No parenthesis on timezone.now
    # because I'm passing the function not the current value
    time_posted = models.DateTimeField(default=timezone.now)
    time_completed = models.DateTimeField(null=True, blank=True)
    time_closed = models.DateTimeField(null=True, blank=True)
    # Relations
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    project = models.ForeignKey('project.Project')
    task = models.ForeignKey('task.Task', null=True, blank=True)
    solution = models.ForeignKey('solution.Solution', null=True,
                                 blank=True, related_name="solution_set")

    objects = PassThroughManager.for_queryset_class(SolutionQuerySet)()

    def __unicode__(self):
        return "%s %s" % (
            self.pk, '/'.join(filter(None, [
                self.is_completed and 'cmp',
                self.is_closed and 'cls',
                self.is_archived and 'arc',
            ])))

    @property
    def followers(self):
        """ Get users for notify.

        :returns: A set of users.

        """
        return set([self.owner] + list(self.iterate_commentators()))

    def save(self, **kwargs):
        """ Notify at creation. """
        created = not self.pk
        super(Solution, self).save(**kwargs)
        if created:
            self.notify_created()
        cache.delete('%s:solutions_tabs' % self.project_id)

    @property
    def default_title(self):
        """ Return a title for the solution.

        Defaults to title of the parent task.

        """
        if self.title:
            return self.title
        else:
            return self.task.title

    def get_impact(self):
        """ Calculate impact, analogous to value of contribution.

        Overrides Voteables base implementation to add the defaulting of
        impact. If there are no valid votes after SOLUTION_REVIEW_PERIOD_SECONDS
        seconds passed award contributor demanded impact.

        :return int: value of contribution

        """
        calculated_impact = super(Solution, self).get_impact()
        frontier = timezone.now() - timezone.timedelta(
            seconds=settings.SOLUTION_REVIEW_PERIOD_SECONDS)
        if self.time_completed < frontier and self.valid_vote_count == 0:
            return self.impact  # demanded impact
        return calculated_impact

    def is_vote_valid(self, vote):
        """ Return whether vote should count.

        Don't count a rejection vote, if the person did not provide
        a comment in the solution review.

        """
        return vote.is_accepted or self.has_commented(vote.voter_id)

    @property
    def valid_vote_count(self):
        """ Return count of valid votes.

        :return int: count of valid votes.

        """
        return len([vote for vote in self.vote_set.all()
                    if self.is_vote_valid(vote)])

    def get_subtask_count(
            self, solution_is_completed=False, solution_is_closed=False,
            task_is_reviewed=False, task_is_accepted=False,
            task_is_closed=False):
        """ Return count of tasks stemming from this solution.

        Keyword arguments :
        solution_is_completed -- whether solutions included in the
            count should be completed.
        solution_is_closed -- whether solutions included in the
            count should be closed.
        task_is_reviewed -- whether tasks included in the count
            should be reviewed.
        task_is_accepted -- whether tasks included in the count
            should be accepted.
        task_is_closed -- whether tasks included in the count
            should be closed.

        """
        subtasks = self.subtask_set.filter(is_reviewed=task_is_reviewed,
                                           is_accepted=task_is_accepted,
                                           is_closed=task_is_closed)
        count = 0
        for subtask in subtasks:
            count += 1  # for the task it self
            count += subtask.get_subtask_count(
                solution_is_completed, solution_is_closed,
                task_is_reviewed, task_is_accepted, task_is_closed)
        return count

    def change_evaluation(self, value):
        """ Change evaluation of solution.

        :param value: new value to set.
        :return:

        """
        if self.impact != value:
            self.notify_evaluation_changed()
            self.impact = value
            self.save()
            self.vote_set.clear()

    def mark_complete(self, impact):
        """ Mark the solution complete.

        :param impact: amount of impact demanded by the contributor for
            the solution.

        """
        self.impact = impact
        self.is_completed = True
        self.time_completed = timezone.now()
        self.save()
        self.notify_complete()

    def mark_incomplete(self):
        """ Mark the solution incomplete.

        Clears vote set.

        """
        self.vote_set.clear()
        self.impact = None
        self.is_completed = False
        self.time_completed = None
        self.save()
        self.notify_incomplete()

    def mark_close(self):
        """ Mark the solution closed. """
        self.is_closed = True
        self.time_closed = timezone.now()
        self.save()

    def mark_open(self):
        """ Mark the solution opened, for reopening. """
        self.is_closed = False
        self.time_closed = None
        self.save()

    def mark_archived(self):
        """ Mark the solution archived. """
        self.is_archived = True
        self.save()
        self.notify(
            self.owner, settings.NOTIFICATION_TYPES.solution_archived, False)

    def notify_evaluation_changed(self):
        """ Send out notifications about the evaluation changing.

        Notify all the people who had previously voted on the solution.

        """
        for vote in self.vote_set.all():
            self.notify(
                vote.voter,
                settings.NOTIFICATION_TYPES.solution_evaluation_changed, False)

    def notify_created(self):
        """ Send out notifications about the solution being posted. """
        # notify parent task owner
        if self.task and self.task.owner_id != self.owner_id:
            self.notify(
                self.task.owner, settings.NOTIFICATION_TYPES.solution_posted,
                True, kwargs={"role": "parent_task"})
        # notify parent solution owner
        elif self.solution and self.solution.owner_id != self.owner_id:
            self.notify(
                self.solution.owner,
                settings.NOTIFICATION_TYPES.solution_posted, True,
                kwargs={"role": "parent_solution"})
        else:  # no parent, notify project admins
            for admin in self.project.admin_set.all():
                if admin.id != self.owner_id:
                    self.notify(
                        admin, settings.NOTIFICATION_TYPES.solution_posted,
                        True, kwargs={"role": "project_admin"})

    def notify_complete(self):
        """ Send out completion notifications. """
        # Notify task owner (dont notify youself)
        if self.task \
                and not self.task.is_closed \
                and self.task.owner_id != self.owner_id:
            self.notify(self.task.owner,
                        settings.NOTIFICATION_TYPES.solution_marked_complete,
                        True, kwargs={"role": "task_owner"})

    def notify_incomplete(self):
        """ Remove completion notifications. """
        if self.task:
            self.delete_notifications(
                self.task.owner,
                settings.NOTIFICATION_TYPES.solution_marked_complete)
        for vote in self.vote_set.all():
            self.delete_notifications(
                vote.voter,
                settings.NOTIFICATION_TYPES.solution_marked_complete)

    def get_notification_url(self, notification):
        """ Return notification target url. """
        from django.core.urlresolvers import reverse
        if settings.NOTIFICATION_TYPES.vote_added == notification.type \
            or settings.NOTIFICATION_TYPES.vote_updated == notification.type \
            or settings.NOTIFICATION_TYPES.solution_evaluation_changed \
                == notification.type:
            return reverse("project:solution:review",
                           args=[self.project.id, self.id])
        else:
            return reverse("project:solution:solution",
                           args=[self.project.id, self.id])

    def get_notification_kwargs(self, notification=None, **kwargs):
        """ Precache notification kwargs.

        :returns: Kwargs dictionary

        """
        python_serializer = serializers.python.Serializer()
        kwargs = super(Solution, self).get_notification_kwargs(
            notification, **kwargs)
        kwargs['owner'] = python_serializer.serialize(
            [self.owner], fields=('username', 'first_name'))[0]
        return kwargs

    # Git related

    def get_parent_reference(self):
        """ Return the parent branch reference string.

        The solution branch should have been checked out from here.

        """
        from git.utils import get_branch_reference
        if self.task and self.task.parent:
            return self.task.parent.get_reference()
        elif self.solution:
            return self.solution.get_reference()
        else:
            return get_branch_reference('master')  # default to master

    def get_parent_pygit_branch(self, pygit_repository):
        """ Return pygit2 Branch object for this solution's parent branch.

        Returns symbolic reference, need to resolve().

        """
        return pygit_repository.lookup_reference(self.get_parent_reference())

    def get_branch_name(self):
        """ Return solution branch name. """
        return "s/%d" % self.id

    def get_reference(self):
        """ Return solution branch reference string. """
        from git.utils import get_branch_reference
        return get_branch_reference(self.get_branch_name())

    def get_pygit_branch(self, pygit_repository):
        """ Return pygit2 Branch object for this solution.

        Returns symbolic reference, need to resolve().

        """
        return pygit_repository.lookup_reference(self.get_reference())

    def get_pygit_solution_range(self, pygit_repository):
        """ Return pygit2 Oid objects representing commit range.

        Returned first is the solution commit, returned second is
        the end commit representing the checkout point.

        """
        from git.utils import get_checkout_oid
        solution_branch_oid = self.get_pygit_branch(
            pygit_repository).resolve().target
        parent_branch_oid = self.get_parent_pygit_branch(
            pygit_repository).resolve().target
        checkout_oid = get_checkout_oid(
            pygit_repository, solution_branch_oid, parent_branch_oid)
        return solution_branch_oid, checkout_oid  # return Oid objects

    def get_pygit_checkout(self, pygit_repository):
        """ Return pygit2 Oid of merge base. """
        _, range_checkout_oid = \
            self.get_pygit_solution_range(pygit_repository)
        return range_checkout_oid

    def get_commit_oid_set(self, pygit_repository):
        """ Return a list of commits for this solution.

        Walks from parent branch's merge base to solution branch's head.
        Returns a list of pygit2 Oid objects representing commits.

        """
        # TODO test when solution branch has not been pushed yet
        from pygit2 import GIT_SORT_TOPOLOGICAL

        solution_branch_oid, checkout_oid = \
            self.get_pygit_solution_range(pygit_repository)
        commits = []
        for commit in pygit_repository.walk(solution_branch_oid,
                                            GIT_SORT_TOPOLOGICAL):
            if commit.hex == checkout_oid.hex:
                break  # reached merge base
            commits.append(commit.oid)
        return commits

    def get_commit_set(self, pygit_repository):
        """ Return a list of pygit2 Commits objects from commit set. """
        from git.holders import CommitHolder
        return (CommitHolder(pygit_repository[oid]) for oid in
                self.get_commit_oid_set(pygit_repository))

    def get_pygit_diff(self, pygit_repository):
        """ Return pygit2 Diff object for the changes done by the solution. """
        # todo write tests
        from git.holders import DiffHolder
        solution_branch_oid, checkout_oid = \
            self.get_pygit_solution_range(pygit_repository)
        return DiffHolder(
            pygit_repository.diff(pygit_repository[checkout_oid],
                                  pygit_repository[solution_branch_oid]))
