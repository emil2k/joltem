from django.db import models
from django.contrib.auth.models import User
from task.models import Task
from project.models import Project

from datetime import datetime


class Solution(models.Model):
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
    # NOTE : No parenthesis on datetime.now because I'm passing the function not the current value
    time_posted = models.DateTimeField(default=datetime.now)
    time_accepted = models.DateTimeField(null=True, blank=True)
    time_completed = models.DateTimeField(null=True, blank=True)
    # Relations
    project = models.ForeignKey(Project)
    task = models.ForeignKey(Task)
    user = models.ForeignKey(User)

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
    def acceptance(self):
        '''
        Impact-weighted percentage of acceptance amongst reviewers
        '''
        votes = self.vote_set.filter(voter_impact__gt=0)
        weighted_sum = 0
        impact_sum = 0
        for vote in votes:
            impact_sum += vote.voter_impact
            if vote.is_accepted:
                weighted_sum += vote.voter_impact
        if impact_sum == 0:
            return 0
        else:
            return int(round(100 * weighted_sum/float(impact_sum)))

    @property
    def impact(self):
        votes = self.vote_set.filter(voter_impact__gt=0)
        weighted_sum = 0
        impact_sum = 0
        for vote in votes:
            impact_sum += vote.voter_impact
            # TODO determine how to count rejected votes
            if vote.is_accepted:
                weighted_sum += vote.voter_impact * vote.vote
        if impact_sum == 0:
            return 0
        else:
            return int(round(10 * weighted_sum/float(impact_sum)))

    @property
    def subtasks(self):
        """
        Count of open subtasks stemming from this solution
        """
        open_subtasks = self.tasks.filter(is_closed=False)
        count = open_subtasks.count()
        for subtask in open_subtasks:
            count += subtask.subtasks
        return count

    def is_owner(self, user):
        """
        Returns whether passed user is the person who posted this solution
        """
        return self.user_id == user.id


class Vote(models.Model):
    """
    Votes cast when solution is marked completed, code is reviewed
    """
    voter_impact = models.BigIntegerField()  # at time of vote
    is_accepted = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    vote = models.SmallIntegerField(null=True, blank=True)  # 0-10 scale of impact of task if accepted
    comment = models.TextField(null=True, blank=True)
    time_voted = models.DateTimeField(default=datetime.now)
    # Relations
    solution = models.ForeignKey(Solution)
    voter = models.ForeignKey(User)

    class Meta:
        unique_together = ("solution","voter")

    def __unicode__(self):
        return str(self.vote)


class VoteComment(models.Model):
    """
    Comments on votes in a solution review
    """
    comment = models.TextField(null=True, blank=True)
    time_commented = models.DateTimeField(default=datetime.now)
    # Relations
    solution = models.ForeignKey(Solution)
    commenter = models.ForeignKey(User)

