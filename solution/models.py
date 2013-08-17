from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes import generic, models as content_type_models
from django.contrib.auth.models import User
from task.models import Task

import logging
logger = logging.getLogger('django')


class Vote(models.Model):
    """
    Vote, abstract class
    """
    voter_impact = models.BigIntegerField()  # at time of vote
    is_accepted = models.BooleanField(default=False)
    magnitude = models.SmallIntegerField(null=True, blank=True)  # represents n in 10^n for the vote, n=1 for satisfactory, n=2 for one star and so on ...
    time_voted = models.DateTimeField(default=timezone.now)
    # Relations
    voter = models.ForeignKey(User)
    # Generic relations
    voteable_type = models.ForeignKey(content_type_models.ContentType)
    voteable_id = models.PositiveIntegerField()
    voteable = generic.GenericForeignKey('voteable_type', 'voteable_id')

    MAXIMUM_MAGNITUDE = 5  # the maximum magnitude for a vote

    def __unicode__(self):
        return str(self.id)

    @property
    def is_rejected(self):
        return not self.is_accepted


class Voteable(models.Model):
    """
    An object that can be voted on for impact determination
    """
    impact = models.BigIntegerField(null=True, blank=True)
    acceptance = models.SmallIntegerField(null=True, blank=True)  # impact-weighted percentage of acceptance
    # Relations
    project = models.ForeignKey('project.Project')
    user = models.ForeignKey(User)
    # Generic relations
    vote_set = generic.GenericRelation(Vote, content_type_field='voteable_type', object_id_field='voteable_id')

    class Meta:
        abstract = True

    def get_acceptance(self):
        """
        Impact-weighted percentage of acceptance amongst reviewers
        """
        votes = self.vote_set.filter(voter_impact__gt=0)
        impact_sum = 0
        weighted_sum = 0
        for vote in votes:
            if not self.is_vote_valid(vote):
                continue
            elif vote.is_accepted:
                weighted_sum += vote.voter_impact
            impact_sum += vote.voter_impact
        if impact_sum == 0:
            return None
        else:
            return int(round(100 * float(weighted_sum)/impact_sum))

    def get_impact(self):
        """
        Calculate impact, analogous to value of contribution
        """
        impact_sum = 0
        weighted_sum = 0
        for vote in self.vote_set.all():
            logger.debug("VOTE : accepted : %s : valid : %s : mag : %d : imp : %d" % (vote.is_accepted, self.is_vote_valid(vote), vote.magnitude, vote.voter_impact))
            if not self.is_vote_valid(vote):
                logger.info("VOTE : not valid")
                continue
            elif vote.is_accepted:
                weighted_sum += vote.voter_impact * self.get_vote_value(vote)
                logger.debug("VOTE : accepted add to weighted sum : %d" % weighted_sum)
            impact_sum += vote.voter_impact
            logger.debug("VOTE : added to impact sum : %d" % impact_sum)
        if impact_sum == 0:
            logger.debug("VOTE : impact sum == 0 : %d" % impact_sum)
            return None
        logger.info("VOTE : return impact : %d / %s" % (weighted_sum, float(impact_sum)))
        logger.info("VOTE : return impact : %s" % int(round(weighted_sum / float(impact_sum))))
        return int(round(weighted_sum / float(impact_sum)))

    def get_impact_distribution(self):
        """
        Impact distribution based on magnitude, with 0 representing a rejected vote
        """
        d = [0] * (1 + Vote.MAXIMUM_MAGNITUDE)
        for vote in self.vote_set.all():
            d[vote.magnitude] += vote.voter_impact
        return d

    def get_impact_integrals(self):
        """
        Calculate impact integrals (integration of the impact distribution from the given magnitude
        to the maximum magnitude) for each magnitude returns a list
        """
        stop = 1 + Vote.MAXIMUM_MAGNITUDE
        d = self.get_impact_distribution()
        ii = [0] * stop
        for magnitude in range(stop):
            # Integrate distribution
            for x in range(magnitude, stop):
                ii[magnitude] += d[x]
        return ii

    def get_impact_integrals_excluding_vote(self, vote):
        """
        Calculate impact integrals, excluding the specified vote
        """
        ii = self.get_impact_integrals()
        for x in range(1 + vote.magnitude):
            ii[x] -= vote.voter_impact
        return ii

    def is_vote_valid(self, vote):
        """
        Determines whether vote should be counted or not
        OVERRIDE in EXTENDING CLASS
        """
        return True

    """
    Thought process ...
    If vote is less than one standard deviation above of the actual magnitude,
    a minimum of 15.9% of the rest of distribution would be between it and the maximum.

    If there is no support at that magnitude it goes down a level to the minimum of 1
    for an accepted vote
    TODO should this go the other way too?
    """
    MAGNITUDE_THRESHOLD = 0.159  # minimum supporting impact integral

    def get_vote_value(self, vote):
        """
        Determines vote value based on the impact distribution of the other votes
        Assumes vote is accepted, so magnitude is greater than 0
        """
        assert vote.magnitude > 0
        logger.debug("GET VOTE VALUE : %d : %d" % (vote.magnitude, vote.voter_impact))
        excluding_total = sum(self.get_impact_distribution()) - vote.voter_impact
        ie = self.get_impact_integrals_excluding_vote(vote)
        if excluding_total > 0:
            for magnitude in reversed(range(1, 1 + vote.magnitude)):
                excluding_integral = ie[magnitude]
                p = float(excluding_integral) / excluding_total
                logger.debug("** %d : %.3f : %d" % (magnitude, p, excluding_integral))
                if p > Voteable.MAGNITUDE_THRESHOLD:
                    return pow(10, magnitude)
        logger.info("** VOTE : defaulted to 10")
        return 10  # default

@receiver([post_save, post_delete], sender=Vote)
def update_metrics(sender, **kwargs):
    """
    Update vote metrics (acceptance and impact) and save to DB
    """
    vote = kwargs.get('instance')
    logger.info("UPDATE METRICS from vote : %s" % vote.magnitude)
    if vote and vote.voteable:
        voteable = vote.voteable
        voteable.acceptance = voteable.get_acceptance()
        voteable.impact = voteable.get_impact()
        voteable.save()


class Solution(Voteable):
    """
    A single task can be worked on by multiple groups at the same time, in different branches for variation.
    """
    # Optional custom title to solution
    title = models.TextField(null=True, blank=True)
    # Description of solution for all involved
    description = models.TextField(null=True, blank=True)
    # Whether solution was accepted by creator of task
    is_accepted = models.BooleanField(default=False)
    # Whether solution was marked completed
    is_completed = models.BooleanField(default=False)
    # Alternative to deletion of solution, to keep all relationships intact
    is_closed = models.BooleanField(default=False)
    # NOTE : No parenthesis on timezone.now because I'm passing the function not the current value
    time_posted = models.DateTimeField(default=timezone.now)
    time_accepted = models.DateTimeField(null=True, blank=True)
    time_completed = models.DateTimeField(null=True, blank=True)
    time_closed = models.DateTimeField(null=True, blank=True)
    # Relations
    task = models.ForeignKey(Task, null=True, blank=True)
    solution = models.ForeignKey("solution.Solution", null=True, blank=True, related_name="solution_set")

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
        subtasks = self.subtask_set.all()
        count = subtasks.count()
        for subtask in subtasks:
            count += subtask.subtasks
        return count

    def is_owner(self, user):
        """
        Returns whether passed user is the person who posted this solution
        """
        return self.user_id == user.id

    def is_acceptor(self, user):
        """
        Returns whether passed user is the person responsible for accepting the solution
        """
        if self.task:
            if not self.task.is_closed:
                return self.task.is_owner(user)
            if self.task.parent:
                if not self.task.parent.is_completed and not self.task.parent.is_closed:
                    return self.task.parent.is_owner(user)
                else:
                    return self.task.parent.is_acceptor(user)
        elif self.solution:
            if not self.solution.is_completed and not self.solution.is_closed:
                return self.solution.is_owner(user)
            else:
                return self.solution.is_acceptor(user)

        return self.project.is_admin(user.id)  # default to project admin

    def has_commented(self, user_id):
        """
        Returns whether passed user has commented on the solution
        """
        # todo write tests for this function
        return Comment.objects.filter(solution_id=self.id, user_id=user_id).count() > 0

    # Git related

    def get_parent_reference(self):
        """
        Get the parent reference, this solution branch should have been checked out from here
        """
        # todo write tests for this function
        from git.utils import get_branch_reference
        if self.task and self.task.parent:
            return self.task.parent.get_reference()
        elif self.solution:
            return self.solution.get_reference()
        else:
            return get_branch_reference('master')  # default to master

    def get_parent_pygit_branch(self, pygit_repository):
        """
        Get pygit2 Branch object for this solution's parent branch on the given repository (pygit object), if it is in repository
        """
        # TODO write tests for this function
        return pygit_repository.lookup_reference(self.get_parent_reference())

    def get_reference(self):
        from git.utils import get_branch_reference
        return get_branch_reference("s/%d" % self.id)

    def get_pygit_branch(self, pygit_repository):
        """
        Get pygit2 Branch object for this solution on the given repository (pygit object), if it is in repository
        """
        # TODO write tests for this function
        return pygit_repository.lookup_reference(self.get_reference())

    def get_commit_set(self, pygit_repository):
        """
        Returns a list of commits for this solution the passed repository (pygit object),
        by walking from appropriate parent branch's merge base.

        Commits are represented by pygit2 Commit objects.
        """
        # todo write some more tests
        from pygit2 import GIT_SORT_TOPOLOGICAL
        solution_branch_oid = self.get_pygit_branch(pygit_repository).resolve().target
        parent_branch_oid = self.get_parent_pygit_branch(pygit_repository).resolve().target
        merge_base_oid = pygit_repository.merge_base(solution_branch_oid, parent_branch_oid)
        commits = []
        for commit in pygit_repository.walk(solution_branch_oid, GIT_SORT_TOPOLOGICAL):
            if commit.hex == merge_base_oid.hex:
                break  # reached merge base
            commits.append(commit.oid)
        return commits


class Comment(Voteable):
    """
    Comments in a solution review
    """
    # TODO make comments more generic, with a commentable base class
    comment = models.TextField(null=True, blank=True)
    time_commented = models.DateTimeField(default=timezone.now)
    # Relations
    solution = models.ForeignKey(Solution)

    def __unicode__(self):
        return str(self.id)


@receiver([post_save, post_delete], sender=Comment)
def update_metrics_from_comment(sender, **kwargs):
    """
    Update vote metrics for a solution, because vote validity depends on whether there is a comment
    """
    comment = kwargs.get('instance')
    logger.info("UPDATE METRICS from comment : %s" % comment)
    if comment and comment.solution:
        voteable = comment.solution
        voteable.acceptance = voteable.get_acceptance()
        voteable.impact = voteable.get_impact()
        voteable.save()