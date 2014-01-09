""" Project's related models. """

from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from joltem.models import Notifying

from project import receivers
from solution.models import Solution

import logging

logger = logging.getLogger('joltem')

NOTIFICATION_TYPE_FROZEN_RATIO = "frozen_ratio"
NOTIFICATION_TYPE_UNFROZEN_RATIO = "unfrozen_ratio"


class Project(Notifying):

    """ Represent Project in Joltem. """

    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)

    # Relations

    admin_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="admin_project_set")
    manager_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="manager_project_set")
    developer_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="developer_project_set")
    subscriber_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='subscriber_project_set')

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

    def notify_frozen_ratio(self, user):
        """ Notify user that impact has been frozen.

        Due to low votes ratio.

        :param user: the user to notify

        """
        self.notify(user, NOTIFICATION_TYPE_FROZEN_RATIO, True)

    def notify_unfrozen_ratio(self, user):
        """ Notify user that impact has been unfrozen.

        Due to raising of votes ratio above the acceptable threshold.

        :param user: the user to notify

        """
        self.notify(user, NOTIFICATION_TYPE_UNFROZEN_RATIO, True)

    def get_notification_text(self, notification):
        """ Return the displayed notification text.

        :param notification: Notification instance
        :return str: notification text

        """
        if notification.type == NOTIFICATION_TYPE_FROZEN_RATIO:
            return "Your votes ratio is low, earning of impact " \
                   "has been frozen on %s" % notification.notifying.title
        elif notification.type == NOTIFICATION_TYPE_UNFROZEN_RATIO:
            return "Votes ratio raised, earning of impact " \
                   "has been unfrozen on %s" % notification.notifying.title
        else:
            return "Project %s updated" % notification.notifying.title

    def get_notification_url(self, notification):
        """ Return the notification url.

        :param notification: Notification instance
        :return str: url target of notification

        """
        return reverse('project:project',
                       args=[notification.notifying.id])


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

    class Meta:
        unique_together = ['project', 'user']

    def get_solutions_qs(self):
        """ Get the solutions eligible for calculating impact.

        :return: queryset of eligible solutions.

        """
        return self.user.solution_set.filter(
            project_id=self.project_id, is_completed=True
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
        except (Ratio.DoesNotExist, Ratio.MultipleObjectsReturned):
            ratio = None
        # Load eligible voteables
        solution_qs = self.get_solutions_qs()
        # Ignore frozen time frame
        if ratio and ratio.is_frozen and ratio.time_frozen:
            solution_qs = solution_qs.filter(time_posted__lt=ratio.time_frozen)
        # Impact from solutions
        for solution in solution_qs:
            impact += solution.get_impact()
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
        except (Ratio.DoesNotExist, Ratio.MultipleObjectsReturned):
            return 0
        else:
            frozen_impact = 0
            # Load eligible voteables
            solution_qs = self.get_solutions_qs()
            # Should be in frozen time frame
            if ratio and ratio.is_frozen and ratio.time_frozen:
                solution_qs = solution_qs.filter(
                    time_posted__gte=ratio.time_frozen)
            else:
                return 0
            # Frozen impact from solutions
            solution_impact = solution_qs.aggregate(
                models.Sum('impact')).get('impact__sum')
            if solution_impact:
                frozen_impact += solution_impact
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

    RATIO_THRESHOLD = 0.5
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
        """ Update frozen state based on current votes ratio.

        State cannot be frozen if it is impossible for a user to achieve a
        votes ratio equal to the RATIO_THRESHOLD. This can happen when a user
        has the majority of completed solutions and there simply isn't enough
        solutions for the user to review.

        """
        if self.votes_ratio is not None \
                and self.is_threshold_possible() \
                and self.votes_ratio < Ratio.RATIO_THRESHOLD:
            self.mark_frozen()
        else:
            self.mark_unfrozen()

    def is_threshold_possible(self):
        """ Determine whether it is possible to achieve minimum votes ratio.

        :return bool: whether it is possible for the user to achieve a votes
            ratio equal to the RATIO_THRESHOLD

        """
        max_out = self.maximum_possible_votes_out()
        max_ratio = self.get_votes_ratio(votes_out=max_out)
        return max_ratio is None or max_ratio >= Ratio.RATIO_THRESHOLD

    # todo test when solution gains vote or validity state changes
    def maximum_possible_votes_out(self):
        """ Calculate the maximum possible votes out.

        Used for determining whether RATIO_THRESHOLD is possible for the user
        in determining whether to freeze impact earning or not.

        Counts the number of completed solutions, not owned by the user, that
        have less than the VOTES_THRESHOLD number of votes therefore making
        it possible for the user to increment the votes out metric via vote.

        :return int: maximum possible votes out

        """
        max_out = 0
        solutions = self.project.solution_set.exclude(owner_id=self.user_id)\
            .filter(is_completed=True)
        for solution in solutions:
            valid_count = 0
            valid_vote = False
            for vote in solution.vote_set.order_by('time_voted'):
                if vote.voter_impact > 0 and solution.is_vote_valid(vote):
                    if valid_count < Ratio.VOTES_THRESHOLD \
                            and vote.voter_id == self.user_id:
                        valid_vote = True
                    valid_count += 1
            if valid_vote:
                max_out += 1
            elif valid_count < Ratio.VOTES_THRESHOLD:
                max_out += 1
        return max_out

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
            self.project.notify_frozen_ratio(self.user)

    def mark_unfrozen(self):
        """ Mark the user impact unfrozen due to low votes ratio.

        Called when the user's vote ratio for the project becomes more
        than or equal to the RATIO_THRESHOLD.

        """
        if self.is_frozen:
            self.is_frozen = False
            self.time_frozen = None
            self.save()
            self.project.notify_unfrozen_ratio(self.user)

    def get_votes_in(self):
        """ Calculate the votes in metric.

        :return int: the votes in metric.

        """
        votes_in = 0
        for solution in self.user.solution_set.filter(
                project_id=self.project_id):
            solution_votes_in = 0
            for vote in solution.vote_set.order_by('time_voted'):
                # Ignore invalid votes
                if not solution.is_vote_valid(vote):
                    continue
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
                voteable_type_id=solution_type.id).exclude(voter_impact=0):
            solution = my_vote.voteable

            # Check that voteable is in the same project.
            if solution.project_id != self.project.id:
                continue

            # Ignore invalid votes
            if not solution.is_vote_valid(my_vote):
                continue

            solution_votes_in = 0

            for vote in solution.vote_set.exclude(voter_impact=0).order_by(
                    'time_voted'):
                # Ignore votes beyond the votes threshold
                if solution_votes_in >= Ratio.VOTES_THRESHOLD:
                    break

                solution_votes_in += 1
                if my_vote.id == vote.id:
                    votes_out += 1

        return votes_out

    def get_votes_ratio(self, votes_out=None, votes_in=None):
        """ Calculate votes ratio.

        :param votes_out: override votes out
        :param votes_in: override votes in
        :return float: the votes ratio metric.

        """
        if votes_out is None:
            votes_out = self.get_votes_out()
        if votes_in is None:
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
