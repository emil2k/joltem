""" Project's related models. """

import operator
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
import logging

from joltem.models import Notifying


logger = logging.getLogger('joltem')


class Project(Notifying):

    """ Represents a project.

    :param title: the displayed title of the project.
    :param description: a detailed description of the project, stored
        in markdown.
    :param is_private: whether project is private, requires invitation
        to view and contribute.
    :param total_shares: the total number of outstanding shares.
    :param impact_shares: the number of shares allocated to back impact.
    :param exchange_periodicity: the number of months between impact exchange
        events.
    :param exchange_magnitude: int from 0-100, representing the % of impact
        that can be exchanged at each exchange event.
    :param date_last_exchange: date of the last exchange event, or the
        initiation of the project exchange sequence.
    :param admin_set: users that can change project settings and have all
        abilities of managers and developers.
    :param manager_set: users that can push to master, develop, and create
        new branches, create repositories, and approve/reject tasks
        unilaterally.
    :param developer_set: users that can push to develop, can merge in
        solution branches.
    :param subscriber_set: users that can follow the project and want to
        receive notification about project.
    :param founder_set: users that are considered founders of project.

    """

    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    is_private = models.BooleanField(default=False)
    total_shares = models.BigIntegerField(default=0)
    impact_shares = models.BigIntegerField(default=0)
    exchange_periodicity = models.SmallIntegerField(default=0)
    exchange_magnitude = models.SmallIntegerField(default=0)
    date_last_exchange = models.DateField(default=timezone.now)

    # Relations

    admin_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="admin_project_set",
        blank=True)
    manager_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="manager_project_set",
        blank=True)
    developer_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="developer_project_set",
        blank=True)
    invitee_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="invitee_project_set",
        blank=True)
    subscriber_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='subscriber_project_set',
        blank=True)
    founder_set = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='founder_project_set',
        blank=True)

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

    def is_invitee(self, user_id):
        """ Check if the user is a invitee of the project.

        :param user_id:
        :return bool:

        """
        return self.invitee_set.filter(id=user_id).exists()

    def has_access(self, user_id):
        """ Determine if the user can access project.

        :param user_id:
        :return bool:

        """
        return not self.is_private \
            or self.is_invitee(user_id) \
            or self.is_developer(user_id) \
            or self.is_manager(user_id) \
            or self.is_admin(user_id)

    def __unicode__(self):
        return self.title

    @property
    def impact_percentage(self):
        """ Return percentage of shares backing impact. """
        if self.total_shares:
            return float(self.impact_shares) * 100 / self.total_shares
        return 0

    def get_open_solutions_count(self):
        """ Calculate the open and incomplete solution count.

        :return int: solution count.

        """
        return self.solution_set.filter(
            is_closed=False, is_completed=False
        ).count()

    def get_completed_solutions_count(self):
        """ Calculate the completed solutions count.

        :return int: solution count.

        """
        return self.solution_set.filter(
            is_completed=True
        ).count()

    def get_open_tasks_count(self):
        """ Calculate the reviewed, accepted, and open tasks count.

        :return int: task count.

        """
        return self.task_set.filter(
            is_accepted=True, is_closed=False
        ).count()

    def get_completed_tasks_count(self):
        """ Calculate the reviewed, accepted, and closed tasks count.

        :return int: task count.

        """
        return self.task_set.filter(
            is_closed=True, is_accepted=True
        ).count()

    def get_feed(self, limit=30):
        """ Compile a recent activity feed for the project.

        Included the most recently updated comments, tasks, and solutions.

        :param limit: number of items to return.
        :return: a list of items, ordered by most recently updated.

        """
        solutions = self.solution_set.select_related('owner', 'task')\
            .order_by('-time_updated')[:limit]
        tasks = self.task_set.select_related('owner')\
            .order_by('-time_updated')[:limit]
        comments = self.comment_set.select_related('owner').prefetch_related(
            'commentable', 'commentable_type').order_by(
            '-time_updated')[:limit]
        return sorted(list(comments) + list(solutions) + list(tasks),
                      key=operator.attrgetter('time_updated'),
                      reverse=True)[:limit]

    def get_overview(self, limit=30):
        """ Compile overview of project.

        :return dict(solutions tasks comments):

        """
        return dict(
            feed=self.get_feed(limit),
            completed_solutions_count=self.get_completed_solutions_count(),
            open_solutions_count=self.get_open_solutions_count(),
            open_tasks_count=self.get_open_tasks_count(),
            completed_tasks_count=self.get_completed_tasks_count(),
        )

    def get_cached_overview(self, limit=30):
        """ Get cached overview of project, if available.

        :return dict: overview

        """
        key = 'project:overview:%s:limit:%d' % (self.id, limit)
        overview = cache.get(key)
        if not overview:
            overview = self.get_overview()
            cache.set(key, overview)
        return overview

    def get_notification_url(self, notification):
        """ Return the notification url.

        :param notification: Notification instance
        :return str: url target of notification

        """
        return reverse('project:project', args=[self.id])


class Impact(models.Model):

    """ Stores project specific impact. """

    impact = models.BigIntegerField(default=0)
    completed = models.IntegerField(default=0)

    # Relations
    project = models.ForeignKey('project.Project')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="impact_set")

    class Meta:
        unique_together = ['project', 'user']

    def __unicode__(self):
        return u'%s : %s' % (self.project.title, self.user.username)

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
        # Impact from solutions
        for solution in self.get_solutions_qs():
            impact += solution.get_impact()
        return impact

    def get_completed(self):
        """ Calculate the number of completed solutions by the user.

        :return int: solution count.

        """
        return self.user.solution_set.filter(
            project_id=self.project.id, is_completed=True).count()


class Equity(models.Model):

    """ Represents a user's project specific ownership.

    :param shares: the number of shares owned by the user on the
        given project.
    :param project:
    :param user:

    """

    shares = models.BigIntegerField(default=0)

    # Relations
    project = models.ForeignKey('project.Project')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="equity_set")

    def __unicode__(self):
        return self.user.username + " : " + self.project.title
