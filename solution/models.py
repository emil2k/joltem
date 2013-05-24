from django.db import models
from django.contrib.auth.models import User
from task.models import Task

from datetime import datetime


class Solution(models.Model):
    """
    A single task can be worked on by multiple groups at the same time, in different branches for variation.
    """
    description = models.TextField()
    # Whether solution was accepted by creator of task
    is_accepted = models.BooleanField(default=False)
    # Whether solution was marked completed by creator of task
    is_completed = models.BooleanField(default=False)
    # Whether solution completion was accepted by creator of task
    is_completion_accepted = models.BooleanField(default=False)
    # NOTE : No parenthesis on datetime.now because I'm passing the function not the current value
    time_posted = models.DateTimeField(default=datetime.now)
    time_edited = models.DateTimeField(null=True, blank=True)
    time_completed = models.DateTimeField(null=True, blank=True)
    time_completion_accepted = models.DateTimeField(null=True, blank=True)
    # Relations
    task = models.ForeignKey(Task)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return str(self.id)

    @property
    def impact(self):
        weighted_sum = 0
        impact_sum = 0
        for vote in self.completionvote_set.all():
            weighted_sum += vote.voter_impact * vote.vote
            impact_sum += vote.voter_impact
        return (weighted_sum/impact_sum) * 10

    def is_owner(self, user):
        """
        Returns whether passed user is the person who posted this solution
        """
        return self.user_id == user.id


class CompletionVote(models.Model):
    """
    Votes cast when solution is marked completed, code is reviewed
    """
    voter_impact = models.BigIntegerField()  # at time of vote
    vote = models.SmallIntegerField()  # 1 or -1
    # Relations
    solution = models.ForeignKey(Solution)
    voter = models.ForeignKey(User)

    class Meta:
        unique_together = ("solution","voter")

    def __unicode__(self):
        return str(self.vote)
