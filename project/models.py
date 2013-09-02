from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete

from project import receivers

import logging
logger = logging.getLogger('joltem')


class Project(models.Model):
    name = models.CharField(max_length=200)  # this is used in the domains, must be lowercase, and only contain a-z and 0-9
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    admin_set = models.ManyToManyField(User)

    def is_admin(self, user_id):
        """
        Check if user is an admin of the project
        """
        return self.admin_set.filter(id=user_id).exists()

    def __unicode__(self):
        return self.name

post_save.connect(receivers.update_project_impact_from_project, sender=Project)
post_delete.connect(receivers.update_project_impact_from_project, sender=Project)


class Impact(models.Model):
    """
    Stores project specific impact
    """
    impact = models.BigIntegerField(null=True, blank=True)
    # Relations
    project = models.ForeignKey('project.Project')
    user = models.ForeignKey(User)

    # Must be above this threshold to count towards impact, an int between 0 and 100
    SOLUTION_ACCEPTANCE_THRESHOLD = 75
    COMMENT_ACCEPTANCE_THRESHOLD = 75

    class Meta:
        unique_together = ['project', 'user']

    def get_impact(self):
        impact = 0
        # The admins of the project start with an impact of 1, for weighted voting to start
        if self.project.is_admin(self.user.id):
            impact += 1
        # Impact from solutions
        for solution in self.user.solution_set.filter(project_id=self.project.id, is_completed=True):
            # Solution acceptance must be higher than this threshold to count towards impact
            if solution.acceptance < Impact.SOLUTION_ACCEPTANCE_THRESHOLD:
                continue
            if solution.impact:
                impact += solution.impact
        # Impact from review comments
        for comment in self.user.comment_set.filter(project_id=self.project.id):
            # Comment acceptance must be higher than this threshold to count towards impact
            if comment.acceptance < Impact.COMMENT_ACCEPTANCE_THRESHOLD:
                continue
            if comment.impact:
                impact += comment.impact
        return impact

post_save.connect(receivers.update_user_metrics_from_project_impact, sender=Impact)
post_delete.connect(receivers.update_user_metrics_from_project_impact, sender=Impact)