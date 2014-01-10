""" Process solutions notifications. """

from django.conf import settings

from joltem.notifications import _NotifyInterface
from joltem.utils import list_string_join


class CommentAdded(_NotifyInterface):

    """ Notify about added comment to solution."""

    ntype = settings.NOTIFICATION_TYPES.comment_added
    model = 'solution.solution'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: Comment added text.

        """
        if notifying is None:
            notifying = self.notification.notifying
        user_id = self.notification.user_id
        first_names = notifying.get_commentator_first_names(
            queryset=notifying.comment_set.select_related('owner').exclude(
                owner_id=user_id).order_by("-time_commented")
        )
        prefix = ''
        if notifying.owner_id == user_id or notifying.author_id == user_id:
            prefix = 'your '
        return "%s commented on %ssolution \"%s\"" % (
            list_string_join(first_names), prefix, notifying.title)
