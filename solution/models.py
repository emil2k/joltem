from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete

from joltem.models import Voteable, Commentable
from joltem import receivers as joltem_receivers

import logging
logger = logging.getLogger('django')


class Solution(Voteable, Commentable):
    """
    A single task can be worked on by multiple groups at the same time, in different branches for variation.
    """
    # Optional custom title to solution
    title = models.TextField(null=True, blank=True)
    # Description of solution for all involved
    description = models.TextField(null=True, blank=True)
    # Whether solution was marked completed
    is_completed = models.BooleanField(default=False)
    # Alternative to deletion of solution, to keep all relationships intact
    is_closed = models.BooleanField(default=False)
    # NOTE : No parenthesis on timezone.now because I'm passing the function not the current value
    time_posted = models.DateTimeField(default=timezone.now)
    time_completed = models.DateTimeField(null=True, blank=True)
    time_closed = models.DateTimeField(null=True, blank=True)
    # Relations
    owner = models.ForeignKey(User)
    project = models.ForeignKey('project.Project')
    task = models.ForeignKey('task.Task', null=True, blank=True)
    solution = models.ForeignKey('solution.Solution', null=True, blank=True, related_name="solution_set")

    def __unicode__(self):
        return str(self.id)

    def is_vote_valid(self, vote):
        # Don't count a vote, if the person did not provide a comment in the solution review
        return vote.is_accepted or self.has_commented(vote.voter_id)

    @property
    def default_title(self):
        """
        Returns either the custom title of the solution, or defaults down to the title of the task
        """
        if self.title:
            return self.title
        else:
            return self.task.title

    @property
    def get_subtask_count(self):
        """
        Count of subtasks stemming from this solution
        """
        subtasks = self.subtask_set.filter(is_accepted=True)
        count = subtasks.count()
        for subtask in subtasks:
            count += subtask.get_subtask_count
        return count

    def has_commented(self, user_id):
        """
        Returns whether passed user has commented on the solution
        """
        return self.comment_set.count() > 0

    def get_notification_text(self, notification):
        return "Solution updated : %s" % self.title

    def get_notification_url(self, url):
        from django.core.urlresolvers import reverse
        return reverse("project:solution:solution", args=[self.project.name, self.id])

    # Git related

    def get_parent_reference(self):
        """
        Get the parent reference, this solution branch should have been checked out from here
        """
        from git.utils import get_branch_reference
        if self.task and self.task.parent:
            return self.task.parent.get_reference()
        elif self.solution:
            return self.solution.get_reference()
        else:
            return get_branch_reference('master')  # default to master

    def get_parent_pygit_branch(self, pygit_repository):
        """
        Get pygit2 Branch object for this solution's parent branch on the
        given repository (pygit object), if it is in repository
        Returns symbolic reference, need to resolve()
        """
        return pygit_repository.lookup_reference(self.get_parent_reference())

    def get_branch_name(self):
        return "s/%d" % self.id

    def get_reference(self):
        from git.utils import get_branch_reference
        return get_branch_reference(self.get_branch_name())

    def get_pygit_branch(self, pygit_repository):
        """
        Get pygit2 Branch object for this solution on the given repository (pygit object), if it is in repository
        Returns symbolic reference, need to resolve()
        """
        return pygit_repository.lookup_reference(self.get_reference())

    def get_pygit_solution_range(self, pygit_repository):
        """
        Returns pygit2 Oid objects representing the start and end commits for the branch
        Returned first is the solution commit, returned second is the end commit representing the checkout point
        """
        from git.utils import get_checkout_oid
        solution_branch_oid = self.get_pygit_branch(pygit_repository).resolve().target
        parent_branch_oid = self.get_parent_pygit_branch(pygit_repository).resolve().target
        checkout_oid = get_checkout_oid(pygit_repository, solution_branch_oid, parent_branch_oid)
        return solution_branch_oid, checkout_oid  # return Oid objects

    def get_pygit_checkout(self, pygit_repository):
        """
        Gets pygit2 Oid of merge base, of the solution branch and it's parent branch from which it should
        """
        solution_branch_oid, range_checkout_oid = self.get_pygit_solution_range(pygit_repository)
        return range_checkout_oid

    def get_commit_oid_set(self, pygit_repository):
        """
        Returns a list of commits for this solution the passed repository (pygit2 object),
        by walking from appropriate parent branch's merge base.

        Commits are represented by pygit2 Oid objects.
        """
        # TODO test when solution branch has not been pushed yet
        from pygit2 import GIT_SORT_TOPOLOGICAL
        solution_branch_oid, checkout_oid = self.get_pygit_solution_range(pygit_repository)
        commits = []
        for commit in pygit_repository.walk(solution_branch_oid, GIT_SORT_TOPOLOGICAL):
            if commit.hex == checkout_oid.hex:
                break  # reached merge base
            commits.append(commit.oid)
        return commits

    def get_commit_set(self, pygit_repository):
        """
        Returns a list of commits represented by pygit2 Commit objects
        """
        from git.holders import CommitHolder
        return (CommitHolder(pygit_repository[oid]) for oid in self.get_commit_oid_set(pygit_repository))

    def get_pygit_diff(self, pygit_repository):
        """
        Get pygit2 Diff object for the changes done by the solution
        """
        # todo write tests
        from git.holders import DiffHolder
        solution_branch_oid, checkout_oid = self.get_pygit_solution_range(pygit_repository)
        return DiffHolder(pygit_repository.diff(pygit_repository[checkout_oid], pygit_repository[solution_branch_oid]))


post_save.connect(joltem_receivers.update_project_impact_from_voteables, sender=Solution)
post_delete.connect(joltem_receivers.update_project_impact_from_voteables, sender=Solution)