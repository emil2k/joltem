""" Project's related models. """

from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from project import receivers
from solution.models import Solution

import logging

logger = logging.getLogger('joltem')


class Project(models.Model):

    """ Represent Project in Joltem. """

    # this is used in the domains, must be lowercase,
    # and only contain a-z and 0-9
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)

    # Relations
    admin_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="admin_project_set")
    manager_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="manager_project_set")
    developer_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="developer_project_set")

    def is_admin(self, user_id):
        """ Check if the user is an admin of the project.

        :param user_id:
        :return bool:

        """
        return self.admin_set.filter(id=user_id).exists()

    def is_manager(self, user_id):
        """ Check if the user is a manager of the project.

        :param user_id:
        :return bool:

        """
        return self.manager_set.filter(id=user_id).exists()

    def is_developer(self, user_id):
        """ Check if the user is a developer of the project.

        :param user_id:
        :return bool:

        """
        return self.developer_set.filter(id=user_id).exists()

    def __unicode__(self):
        return self.name

    def get_overview(self, limit=10):
        """ Overview self.

        :return dict(solutions tasks comments):

        """
        solutions = self.solution_set.select_related('owner', 'task')\
            .order_by('-time_updated')[:limit]

        open_solutions_count = self.solution_set.filter(
            is_closed=False, is_completed=False
        ).count()

        completed_solutions_count = self.solution_set.filter(
            is_completed=True
        ).count()

        tasks = self.task_set.select_related('author')\
            .order_by('-time_updated')[:limit]

        open_tasks_count = self.task_set.filter(
            is_accepted=True, is_closed=False
        ).count()

        completed_tasks_count = self.task_set.filter(
            is_closed=True, is_accepted=True
        ).count()

        comments = self.comment_set.select_related('owner').prefetch_related(
            'commentable', 'commentable_type').order_by(
            '-time_updated')[:limit]

        return dict(
            comments=comments,
            completed_solutions_count=completed_solutions_count,
            open_solutions_count=open_solutions_count,
            open_tasks_count=open_tasks_count,
            completed_tasks_count=completed_tasks_count,
            solutions=solutions,
            tasks=tasks,
        )


post_save.connect(receivers.update_project_impact_from_project, sender=Project)
post_delete.connect(
    receivers.update_project_impact_from_project, sender=Project)


class Impact(models.Model):

    """ Stores project specific impact. """

    impact = models.BigIntegerField(default=0)
    frozen_impact = models.BigIntegerField(default=0)

    # Relations
    project = models.ForeignKey('project.Project')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="impact_set")

    # Must be above this threshold to count towards impact, an int between 0
    # and 100
    SOLUTION_ACCEPTANCE_THRESHOLD = 75
    COMMENT_ACCEPTANCE_THRESHOLD = 75

    class Meta:
        unique_together = ['project', 'user']

    def get_solutions_qs(self):
        """ Get the solutions eligible for calculating impact.

        :return: queryset of eligible solutions.

        """
        return self.user.solution_set.filter(
            project_id=self.project_id, is_completed=True,
            acceptance__gte=Impact.SOLUTION_ACCEPTANCE_THRESHOLD
        ).exclude(impact=None)

    def get_comments_qs(self):
        """ Get the comments eligible for calculating impact.

        :return: queryset of eligible comments.

        """
        return self.user.comment_set.filter(
            project_id=self.project_id,
            acceptance__gte=Impact.COMMENT_ACCEPTANCE_THRESHOLD,
        ).exclude(impact=None)

    def get_impact(self):
        """ Calculate impact.

        :return int:

        """
        impact = 0
        # The admins of the project start with an impact of 1, for weighted
        # voting to start
        if self.project.is_admin(self.user.id):
            impact += 1
        try:
            ratio = Ratio.objects.get(
                user_id=self.user.id, project_id=self.project.id)
        except Ratio.DoesNotExist, Ratio.MultipleObjectsReturned:
            ratio = None
        # Load eligible voteables
        solution_qs = self.get_solutions_qs()
        comment_qs = self.get_comments_qs()
        # Ignore frozen time frame
        if ratio and ratio.is_frozen and ratio.time_frozen:
            solution_qs = solution_qs.filter(time_posted__lt=ratio.time_frozen)
            comment_qs = comment_qs.filter(time_commented__lt=ratio.time_frozen)
        # Impact from solutions
        solution_impact = solution_qs.aggregate(
            models.Sum('impact')).get('impact__sum')
        # Impact from review comments
        comment_impact = comment_qs.aggregate(
            models.Sum('impact')).get('impact__sum')
        if solution_impact:
            impact += solution_impact
        if comment_impact:
            impact += comment_impact
        return impact

    def get_frozen_impact(self):
        """ Calculate frozen impact.

        This the amount impact that has been earned, but is frozen until
        certain criteria are met, like raising the vote ratio above an
        acceptable threshold.

        :return int:

        """
        try:
            ratio = Ratio.objects.get(
                user_id=self.user.id, project_id=self.project.id)
        except Ratio.DoesNotExist, Ratio.MultipleObjectsReturned:
            return 0
        else:
            frozen_impact = 0
            # Load eligible voteables
            solution_qs = self.get_solutions_qs()
            comment_qs = self.get_comments_qs()
            # Should be in frozen time frame
            if ratio and ratio.is_frozen and ratio.time_frozen:
                solution_qs = solution_qs.filter(
                    time_posted__gte=ratio.time_frozen)
                comment_qs = comment_qs.filter(
                    time_commented__gte=ratio.time_frozen)
            else:
                return 0
            # Frozen impact from solutions
            solution_impact = solution_qs.aggregate(
                models.Sum('impact')).get('impact__sum')
            # Frozen impact from comments
            comment_impact = comment_qs.aggregate(
                models.Sum('impact')).get('impact__sum')
            if solution_impact:
                frozen_impact += solution_impact
            if comment_impact:
                frozen_impact += comment_impact
            return frozen_impact

post_save.connect(
    receivers.update_user_metrics_from_project_impact, sender=Impact)
post_delete.connect(
    receivers.update_user_metrics_from_project_impact, sender=Impact)


class Ratio(models.Model):

    """ Stores project specific vote ratio.

    The votes_in metric is roughly a count of votes received by the user
    on his completed solutions in the project. Likewise the votes_out
    metric is roughly the count of votes made by the user on other people's
    completed. The votes_ratio metric is simply the votes_out divided
    by the votes_in and is used to couple the incentive to earn impact
    with reviewing other people's work.

    For both, votes while having no impact don't count and only
    VOTES_THRESHOLD number of votes can count per solution.

    If a user's votes_ratio dips below the RATIO_THRESHOLD, their project
    specific impact is frozen at that time. Freezing of impact, means the
    user will be unable to earn any impact from voteables ( comments and
    solutions ) posted on the project after the time of freezing until
    their project votes_ratio is raised above or equal to the RATIO_THRESHOLD,
    unfreezing the user's impact.

    """

    votes_in = models.IntegerField(default=0)
    votes_out = models.IntegerField(default=0)
    votes_ratio = models.FloatField(null=True)

    is_frozen = models.BooleanField(default=False)
    time_frozen = models.DateTimeField(null=True, blank=True)

    # Relations
    project = models.ForeignKey('project.Project')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="vote_ratio_set")

    RATIO_THRESHOLD = 1.0
    VOTES_THRESHOLD = 5
    INFINITY = 1000.0 * 1000.0

    class Meta:
        unique_together = ['project', 'user']

    @classmethod
    def update(cls, project_id, user_id):
        """ Update voter ratio metrics.

        :param cls:
        :param project_id:
        :param user_id:
        :return Ratio: returns the Ratio instance that was updated

        """
        (ratio, _) = cls.objects.get_or_create(
            project_id=project_id,
            user_id=user_id
        )
        ratio.votes_in = ratio.get_votes_in()
        ratio.votes_out = ratio.get_votes_out()
        ratio.votes_ratio = ratio.get_votes_ratio()
        ratio.save()
        ratio.update_frozen_state()
        return ratio

    def update_frozen_state(self):
        """ Update frozen state based on current votes ratio. """
        if self.votes_ratio is not None \
                and self.votes_ratio < Ratio.RATIO_THRESHOLD:
            self.mark_frozen()
        else:
            self.mark_unfrozen()

    def mark_frozen(self):
        """ Mark the user impact frozen due to low votes ratio.

        Called when the user's vote ratio for the project goes lower
        than the RATIO_THRESHOLD.

        Only update time_frozen and save() if not frozen.

        """
        if not self.is_frozen:
            self.is_frozen = True
            self.time_frozen = timezone.now()
            self.save()

    def mark_unfrozen(self):
        """ Mark the user impact unfrozen due to low votes ratio.

        Called when the user's vote ratio for the project becomes more
        than or equal to the RATIO_THRESHOLD.

        """
        if self.is_frozen:
            self.is_frozen = False
            self.time_frozen = None
            self.save()

    def get_votes_in(self):
        """ Calculate the votes in metric.

        :return int: the votes in metric.

        """
        votes_in = 0
        for solution in self.user.solution_set.filter(
                project_id=self.project_id):
            solution_votes_in = 0
            for vote in solution.vote_set.order_by('time_voted'):
                # Ignore votes from people with no impact
                if vote.voter_impact == 0:
                    continue
                # Ignore votes beyond the votes threshold
                if solution_votes_in < Ratio.VOTES_THRESHOLD:
                    solution_votes_in += 1
                    votes_in += 1
                else:
                    break
        return votes_in

    def get_votes_out(self):
        """ Calculate the votes out metric.

        :return int: the votes out metric.

        """
        votes_out = 0
        solution_type = ContentType.objects.get_for_model(Solution)
        for my_vote in self.user.vote_set.select_related('voteable').filter(
                voteable_type_id=solution_type.id):
            # Check that voteable is in the same project.
            if my_vote.voteable.project_id != self.project.id:
                continue
            # Ignore my votes with no impact
            if my_vote.voter_impact == 0:
                continue
            solution = my_vote.voteable
            solution_votes_in = 0
            for vote in solution.vote_set.order_by('time_voted'):
                # Ignore votes from people with no impact
                if vote.voter_impact == 0:
                    continue
                # Ignore votes beyond the votes threshold
                if solution_votes_in < Ratio.VOTES_THRESHOLD:
                    solution_votes_in += 1
                    if my_vote.id == vote.id:
                        votes_out +=1
                else:
                    break
        return votes_out

    def get_votes_ratio(self):
        """ Calculate votes ratio.

        :return float: the votes ratio metric.

        """
        votes_out = self.get_votes_out()
        votes_in = self.get_votes_in()
        if votes_in:
            return float(votes_out) / votes_in
        elif votes_out:
            return Ratio.INFINITY
        else:
            return None

post_save.connect(
    receivers.update_project_impact_from_project_ratio, sender=Ratio)
post_delete.connect(
    receivers.update_project_impact_from_project_ratio, sender=Ratio)
