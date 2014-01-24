""" Support comments. """

import logging

from django.db import models
from django.conf import settings
from django.contrib.contenttypes import generic, models as content_type_models
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete
from django.utils import timezone

from joltem import receivers
from joltem.models.notifications import Notifying
from joltem.models.generic import Owned, ProjectContext, Updatable

logger = logging.getLogger('django')


# Comment related

class Comment(Owned, ProjectContext, Updatable):

    """ Comments in a solution review. """

    model_name = "comment"

    comment = models.TextField(null=True, blank=True)
    time_commented = models.DateTimeField(default=timezone.now)
    # Relations
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    project = models.ForeignKey('project.Project')
    # Generic relations
    commentable_type = models.ForeignKey(content_type_models.ContentType)
    commentable_id = models.PositiveIntegerField()
    commentable = generic.GenericForeignKey(
        'commentable_type', 'commentable_id')

    class Meta:
        app_label = "joltem"

    def __unicode__(self):
        return str(self.comment)

    def get_comment_url(self):
        """ Get anchor link to this comment.

        :return str:

        """
        from django.core.urlresolvers import reverse
        from solution.models import Solution
        # Depends on the commentable type
        anchor = lambda path: path + \
            "#comment-%s" % self.id  # add a comment anchor
        if self.commentable_type_id == \
                ContentType.objects.get_for_model(Solution).id:
            return anchor(reverse(
                "project:solution:solution", args=[self.project.id,
                                                   self.commentable_id]))
        # it is a Task
        return anchor(reverse(
            "project:task:task", args=[
                self.project_id, self.commentable_id]))

    def get_notification_kwargs(self, notification=None, **kwargs):
        """ Prepare notification kwargs.

        :returns: dict

        """
        return dict(
            owner_id=self.owner_id, owner_name=self.owner.first_name,
            url=self.get_comment_url())


post_save.connect(
    receivers.update_solution_metrics_from_comment, sender=Comment)
post_delete.connect(
    receivers.update_solution_metrics_from_comment, sender=Comment)

post_save.connect(
    receivers.update_project_metrics_from_comment, sender=Comment)
post_delete.connect(
    receivers.update_project_metrics_from_comment, sender=Comment)

post_save.connect(
    receivers.update_project_impact_from_voteables, sender=Comment)
post_delete.connect(
    receivers.update_project_impact_from_voteables, sender=Comment)


class Commentable(Notifying, Owned, ProjectContext):

    """ Abstract, an object that can be commented on. """

    # Generic relations
    comment_set = generic.GenericRelation(
        'joltem.Comment', content_type_field='commentable_type',
        object_id_field='commentable_id')

    class Meta:
        abstract = True

    def has_commented(self, user_id):
        """ Return whether passed user has commented on this commentable.

        :param user_id: user id of commentator

        """
        return self.comment_set.filter(owner_id=user_id).exists()

    def add_comment(self, commentator, comment_text):
        """ Add comment to commentable, returns comment.

        :return Comment:

        """
        comment = Comment(
            time_commented=timezone.now(),
            project=self.project,
            owner=commentator,
            commentable=self,
            comment=comment_text
        )
        comment.save()
        self.notify_comment_added(comment)
        return comment

    def notify_comment_added(self, comment):
        """ Notify other commentators of comment, and owner of notifying. """

        for user in self.followers:
            if user == comment.owner:
                continue
            self.notify(user, settings.NOTIFICATION_TYPES.comment_added, True)

    def iterate_commentators(self, queryset=None, exclude=None):
        """ Iterate through comments and return distinct commentators.

        :param exclude: dict with exclude kwargs

        """
        if queryset is None:
            queryset = self.comment_set.select_related('owner')

        if not exclude is None:
            queryset = queryset.exclude(**exclude)

        commentator_ids = []
        for comment in queryset:
            if not comment.owner_id in commentator_ids:
                commentator_ids.append(comment.owner_id)
                yield comment.owner

    def get_commentator_first_names(self, queryset=None, exclude=None):
        """ Return a distinct list of the commentator first names.

        :return list:

        """
        return [commentator.first_name for commentator in
                self.iterate_commentators(queryset=queryset, exclude=exclude)]

    @property
    def followers(self):
        """ Get users for notify.

        :returns: A set of commentators.

        """
        return set(self.iterate_commentators())
