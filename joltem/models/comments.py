""" Support comments. """

import logging

from django.db import models
from django.conf import settings
from django.contrib.contenttypes import generic, models as content_type_models
from django.db.models.signals import post_save, post_delete
from django.utils import timezone

from joltem import receivers
from joltem.models.votes import Voteable
from joltem.models.notifications import Notifying
from joltem.models.generic import Owned, ProjectContext, Updatable

logger = logging.getLogger('django')


# Comment related

NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL = "comment_marked_helpful"


class Comment(Voteable, Updatable):

    """ Comments in a solution review. """

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

    def notify_vote_added(self, vote):
        """ Override to only notify of "Helpful" or positive votes. """

        if vote.is_accepted:
            self.notify(self.owner,
                        NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL, True)

    def notify_vote_updated(self, vote, old_vote_magnitude):
        """ Override to disable.

        there should be no notifications when votes are updated on comments.
        Except when a vote goes from accepted to

        """
        if vote.is_accepted and old_vote_magnitude == 0:  # became accepted
            self.notify(self.owner,
                        NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL, True)
        elif vote.is_rejected and old_vote_magnitude > 0:  # became rejected
            # Check if there is any other positive votes
            positive_votes = self.get_voters(
                queryset=self.vote_set.filter(is_accepted=True),
                exclude=[vote.voter]
            )
            if len(positive_votes) == 0:
                self.delete_notifications(
                    self.owner, NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL)

    def get_notification_text(self, notification=None):
        """ Get text notification.

        :return str:

        """
        from joltem.utils import list_string_join

        if notification and NOTIFICATION_TYPE_COMMENT_MARKED_HELPFUL == notification.type: # noqa
            # Get first names of all people who marked the comment helpful
            first_names = self.get_voter_first_names(
                queryset=self.vote_set.filter(
                    is_accepted=True).order_by("-time_voted"),
                exclude=[notification.user]
            )
            return "%s marked your comment helpful" % list_string_join(
                first_names)

        return "Comment updated"  # should not resort to this

    def get_notification_url(self, notification):
        """ Get notificaion URL.

        :return str:

        """
        return self.get_comment_url()

    def get_comment_url(self):
        """ Get anchor link to this comment.

        :return str:

        """
        from django.core.urlresolvers import reverse
        from solution.models import Solution
        # Depends on the commentable type
        anchor = lambda path: path + \
            "#comment-%s" % self.id  # add a comment anchor
        if isinstance(self.commentable, Solution):
            return anchor(reverse(
                "project:solution:solution", args=[self.project.name,
                                                   self.commentable_id]))
        else:  # it is a Task
            return anchor(reverse(
                "project:task:task", args=[self.project.name,
                                           self.commentable_id]))


post_save.connect(
    receivers.update_solution_metrics_from_comment, sender=Comment)
post_delete.connect(
    receivers.update_solution_metrics_from_comment, sender=Comment)

post_save.connect(
    receivers.update_project_impact_from_voteables, sender=Comment)
post_delete.connect(
    receivers.update_project_impact_from_voteables, sender=Comment)

NOTIFICATION_TYPE_COMMENT_ADDED = "comment_added"


class Commentable(Notifying, Owned, ProjectContext):

    """ Abstract, an object that can be commented on. """

    # Generic relations
    comment_set = generic.GenericRelation(
        'joltem.Comment', content_type_field='commentable_type',
        object_id_field='commentable_id')

    class Meta:
        abstract = True

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
        if comment.owner_id != self.owner.id:  # notify owner
            self.notify(self.owner, NOTIFICATION_TYPE_COMMENT_ADDED, True)
        for commentator in self.iterate_commentators():
            if commentator.id != self.owner.id \
                    and commentator.id != comment.owner_id:
                self.notify(commentator, NOTIFICATION_TYPE_COMMENT_ADDED, True)

    def iterate_commentators(self, queryset=None, exclude=None):
        """ Iterate through comments and return distinct commentators. """
        if exclude is None:
            exclude = []

        queryset = self.comment_set.all() if queryset is None else queryset
        commentator_ids = []
        for comment in queryset:
            if comment.owner in exclude:
                continue
            if not comment.owner.id in commentator_ids:
                commentator_ids.append(comment.owner.id)
                yield comment.owner

    def get_commentators(self, queryset=None, exclude=None):
        """ Return a distinct list of commentators.

        :return list:

        """
        return [commentator for commentator in self.iterate_commentators(
            queryset=queryset, exclude=exclude)]

    def get_commentator_first_names(self, queryset=None, exclude=None):
        """ Return a distinct list of the commentator first names.

        :return list:

        """
        return [commentator.first_name for commentator in self.get_commentators(
            queryset=queryset, exclude=exclude)]
