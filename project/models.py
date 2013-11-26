""" Project's related models. """

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.conf import settings

from project import receivers

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
    admin_set = models.ManyToManyField(settings.AUTH_USER_MODEL)

    def is_admin(self, user_id):
        """ Check if user is an admin of the project.

        :return bool:

        """
        return self.admin_set.filter(id=user_id).exists()

    def __unicode__(self):
        return self.name

    def get_overview(self, limit=10):
        """ Overview self.

        :return dict(solutions tasks comments):

        """
        solutions = self.solution_set.select_related('owner')\
            .order_by('-time_updated')[:limit]

        tasks = self.task_set.select_related('author')\
            .order_by('-time_updated')[:limit]

        comments = self.comment_set.select_related('owner', 'commentable')\
            .order_by('-time_updated')[:limit]

        return dict(solutions=solutions, tasks=tasks, comments=comments)


post_save.connect(receivers.update_project_impact_from_project, sender=Project)
post_delete.connect(
    receivers.update_project_impact_from_project, sender=Project)


class Impact(models.Model):

    """ Stores project specific impact. """

    impact = models.BigIntegerField(null=True, blank=True)

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

    def get_impact(self):
        """ Calculate impact.

        :return int:

        """
        impact = 0
        # The admins of the project start with an impact of 1, for weighted
        # voting to start
        if self.project.is_admin(self.user.id):
            impact += 1

        # Impact from solutions
        solution_impact = self.user.solution_set.filter(
            project_id=self.project_id, is_completed=True,
            acceptance__gte=Impact.SOLUTION_ACCEPTANCE_THRESHOLD
        ).exclude(impact=None).aggregate(
            models.Sum('impact')).get('impact__sum')

        if solution_impact:
            impact += solution_impact

        # Impact from review comments
        comment_impact = self.user.comment_set.filter(
            project_id=self.project_id,
            acceptance__gte=Impact.COMMENT_ACCEPTANCE_THRESHOLD,
        ).exclude(impact=None).aggregate(
            models.Sum('impact')).get('impact__sum')

        if comment_impact:
            impact += comment_impact

        return impact

post_save.connect(
    receivers.update_user_metrics_from_project_impact, sender=Impact)
post_delete.connect(
    receivers.update_user_metrics_from_project_impact, sender=Impact)
