import logging

from django.db import models
from django.contrib.contenttypes import generic, models as content_type_models
from django.db.models.signals import post_save, post_delete
from django.utils import timezone

from joltem import receivers
from joltem.models.votes import Voteable
from joltem.models.notifications import Notifying

logger = logging.getLogger('django')


# Comment related

class Comment(Voteable):
    """
    Comments in a solution review
    """
    comment = models.TextField(null=True, blank=True)
    time_commented = models.DateTimeField(default=timezone.now)
    # Generic relations
    commentable_type = models.ForeignKey(content_type_models.ContentType)
    commentable_id = models.PositiveIntegerField()
    commentable = generic.GenericForeignKey('commentable_type', 'commentable_id')

    class Meta:
        app_label = "joltem"

    def __unicode__(self):
        return str(self.comment)


post_save.connect(receivers.update_solution_metrics_from_comment, sender=Comment)
post_delete.connect(receivers.update_solution_metrics_from_comment, sender=Comment)

post_save.connect(receivers.update_project_impact_from_voteables, sender=Comment)
post_delete.connect(receivers.update_project_impact_from_voteables, sender=Comment)


class Commentable(Notifying):
    """
    Abstract, an object that can be commented on
    """
    # Generic relations
    comment_set = generic.GenericRelation('joltem.Comment', content_type_field='commentable_type', object_id_field='commentable_id')

    class Meta:
        abstract = True

    def iterate_commentators(self):
        """
        Iterate through comments and return distinct commentators
        """
        commentator_ids = []
        for comment in self.comment_set.all():
            if not comment.user.id in commentator_ids:
                commentator_ids.append(comment.user.id)
                yield comment.user

    @property
    def commentator_set(self):
        """
        Return a distinct list of commentators
        """
        return [commentator for commentator in self.iterate_commentators()]