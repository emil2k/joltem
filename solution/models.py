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
        weighted_sum = 0
        impact_sum = 0
        for vote in votes:
            # Don't count a negative vote if voter didn't provide a comment
            if not vote.is_accepted and not self.has_commented(vote.voter_id):
                continue
            impact_sum += vote.voter_impact
            if vote.is_accepted:
                weighted_sum += vote.voter_impact
        if impact_sum <= 0:
            return None
        else:
            return int(round(100 * float(weighted_sum)/impact_sum))

    def get_impact(self):
        """
        Calculate impact, analogous to value of contribution
        """
        # TODO determine proper vote for each vote
        total_impact = 0
        weighted_sum = 0
        for vote in self.vote_set.all():
            total_impact += vote.voter_impact
            if vote.is_accepted:
                weighted_sum += vote.voter_impact * self.get_vote_value(vote)
        if total_impact == 0:
            return None
        return int(weighted_sum / float(total_impact))

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

    # If vote was within one standard deviation of the actual magnitude,
    # a minimum of 15.9% of the rest of distribution would be between it and the maximum
    # TODO should this go the other way too?
    MAGNITUDE_THRESHOLD = 0.159  # minimum supporting impact integral

    def get_vote_value(self, vote):
        """
        Determines vote value based on the impact distribution of the other votes
        """
        # TODO determine effective magnitude
        return pow(10, vote.magnitude)


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
    # Whether solution was marked completed by creator of task
    is_completed = models.BooleanField(default=False)
    # NOTE : No parenthesis on timezone.now because I'm passing the function not the current value
    time_posted = models.DateTimeField(default=timezone.now)
    time_accepted = models.DateTimeField(null=True, blank=True)
    time_completed = models.DateTimeField(null=True, blank=True)
    # Relations
    task = models.ForeignKey(Task)

    def __unicode__(self):
        return str(self.id)

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
    def subtask_set(self):
        """
        Count of open subtasks stemming from this solution
        """
        open_subtasks = self.tasks.all()
        count = open_subtasks.count()
        for subtask in open_subtasks:
            count += subtask.subtasks
        return count

    def is_owner(self, user):
        """
        Returns whether passed user is the person who posted this solution
        """
        return self.user_id == user.id

    def has_commented(self, user_id):
        """
        Returns whether passed user has commented on the solution
        """
        return Comment.objects.filter(solution_id=self.id, user_id=user_id).count() > 0


class Comment(Voteable):
    """
    Comments in a solution review
    """
    # TODO make comments more generic
    comment = models.TextField(null=True, blank=True)
    time_commented = models.DateTimeField(default=timezone.now)
    # Relations
    solution = models.ForeignKey(Solution)

    def __unicode__(self):
        return str(self.id)