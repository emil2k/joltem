import logging

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic, models as content_type_models
from django.db.models.signals import post_save, post_delete
from django.utils import timezone

from joltem import receivers
from joltem.models.votes import Voteable
from joltem.models.notifications import Notifying
from joltem.models.generic import Owned, ProjectContext

logger = logging.getLogger('django')


# Comment related

class Comment(Voteable):
    """
    Comments in a solution review
    """
    comment = models.TextField(null=True, blank=True)
    time_commented = models.DateTimeField(default=timezone.now)
    # Relations
    owner = models.ForeignKey(User)
    project = models.ForeignKey('project.Project')
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


class Commentable(Notifying, Owned, ProjectContext):
    """
    Abstract, an object that can be commented on
    """
    # Generic relations
    comment_set = generic.GenericRelation('joltem.Comment', content_type_field='commentable_type', object_id_field='commentable_id')

    NOTIFICATION_TYPE_COMMENT_ADDED = "comment_added"

    class Meta:
        abstract = True

    def add_comment(self, commentator, comment_text):
        """
        Adds comment to commentable, returns comment
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
        """
        Notify other commentators of comment, and the owner of the notifying
        """
        if comment.owner_id != self.owner.id:  # notify owner
            self.notify(self.owner, type=Commentable.NOTIFICATION_TYPE_COMMENT_ADDED)
        for commentator in self.iterate_commentators():
            if commentator.id != self.owner.id \
                    and commentator.id != comment.owner_id:
                self.notify(commentator, type=Commentable.NOTIFICATION_TYPE_COMMENT_ADDED)

    def iterate_commentators(self, queryset=None, exclude=[]):
        """
        Iterate through comments and return distinct commentators
        """
        queryset = self.comment_set.all() if not queryset else queryset
        commentator_ids = []
        for comment in queryset:
            if comment.owner in exclude:
                continue
            if not comment.owner.id in commentator_ids:
                commentator_ids.append(comment.owner.id)
                yield comment.owner

    def get_commentators(self, queryset=None, exclude=[]):
        """
        Return a distinct list of commentators
        """
        return [commentator for commentator in self.iterate_commentators(queryset=queryset, exclude=exclude)]

    def get_commentator_first_names(self, queryset=None, exclude=[]):
        """
        Returns a distinct list of the commentator first names
        """
        return [commentator.first_name for commentator in self.get_commentators(queryset=queryset, exclude=exclude)]