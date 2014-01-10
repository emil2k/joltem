""" Process projects notifications. """

from django.conf import settings

from joltem.notifications import _NotifyInterface


class FrozenRatio(_NotifyInterface):

    """ Notify about ratio is frozen."""

    ntype = settings.NOTIFICATION_TYPES.frozen_ratio
    model = 'project.project'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: Comment added text.

        """
        try:
            title = self.notification.kwargs['notifying']['fields']['title']
        except (KeyError, TypeError):
            title = notifying.title
        return "Your votes ratio is low, earning of impact " \
               "has been frozen on %s" % title


class UnFrozenRatio(_NotifyInterface):

    """ Notify about ratio is unfrozen."""

    ntype = settings.NOTIFICATION_TYPES.unfrozen_ratio
    model = 'project.project'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: Comment added text.

        """
        try:
            title = self.notification.kwargs['notifying']['fields']['title']
        except (KeyError, TypeError):
            title = notifying.title
        return "Votes ratio raised, earning of impact " \
               "has been unfrozen on %s" % title
