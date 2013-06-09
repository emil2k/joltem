from django.db import models
from django.contrib.auth.models import User
from task.models import Task

from datetime import datetime


class Solution(models.Model):
    """
    A single task can be worked on by multiple groups at the same time, in different branches for variation.
    """
    # Users application to solve task
    application = models.TextField()
    # Description of solution for all involved
    description = models.TextField(null=True, blank=True)
    # Whether solution was accepted by creator of task
    is_accepted = models.BooleanField(default=False)
    # Whether solution was marked completed by creator of task
    is_completed = models.BooleanField(default=False)
    # Whether solution completion was accepted by creator of task
    is_completion_accepted = models.BooleanField(default=False)
    # NOTE : No parenthesis on datetime.now because I'm passing the function not the current value
    time_posted = models.DateTimeField(default=datetime.now)
    time_accepted = models.DateTimeField(null=True, blank=True)
    time_completed = models.DateTimeField(null=True, blank=True)
    time_completion_accepted = models.DateTimeField(null=True, blank=True)
    # Relations
    task = models.ForeignKey(Task)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return str(self.id)

    @property
    def impact(self):
        votes = self.completionvote_set.all()
        if votes:
            weighted_sum = 0
            impact_sum = 0
            for vote in votes:
                weighted_sum += vote.voter_impact * vote.vote
                impact_sum += vote.voter_impact
            return int(round(10 * weighted_sum/float(impact_sum)))
        else:
            return 0

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
    time_voted = models.DateTimeField(default=datetime.now)
    # Relations
    solution = models.ForeignKey(Solution)
    voter = models.ForeignKey(User)

    class Meta:
        unique_together = ("solution","voter")

    def __unicode__(self):
        return str(self.vote)
