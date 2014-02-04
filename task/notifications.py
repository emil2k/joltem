""" Process tasks notifications. """

from django.conf import settings

from joltem.notifications import _NotifyInterface
from joltem.utils import list_string_join


class CommentAdded(_NotifyInterface):

    """ Notify about added comment to task."""

    ntype = settings.NOTIFICATION_TYPES.comment_added
    model = 'task.task'

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
        if notifying.owner_id == user_id:
            prefix = 'your '
        return "%s commented on %stask \"%s\"" % (
            list_string_join(first_names), prefix, notifying.title)


class TaskPosted(_NotifyInterface):

    """ Notify about posted a task."""

    ntype = settings.NOTIFICATION_TYPES.task_posted
    model = 'task.task'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: Text about task posted.

        """
        owner_name = self.notification.kwargs['owner']['fields']['first_name'] # noqa
        if notifying is None:
            notifying = self.notification.notifying

        if self.notification.kwargs["role"] == "parent_solution":
            return "%s posted a task on your solution \"%s\"" % (
                owner_name, notifying.parent.default_title)

        if self.notification.kwargs["role"] == "project_admin":
            return "%s posted a task" % owner_name


class TaskAccepted(_NotifyInterface):

    """ Notify about accepted a task."""

    ntype = settings.NOTIFICATION_TYPES.task_accepted
    model = 'task.task'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: Text about task posted.

        """
        user_id = self.notification.user_id
        owner_id = self.notification.kwargs['owner']['pk']
        title = self.notification.kwargs['notifying']['fields']['title'] # noqa
        if owner_id == user_id:
            return "Your task \"%s\" was accepted" % title
        return "Task \"%s\" was accepted" % title


class TaskRejected(_NotifyInterface):

    """ Notify about accepted a task."""

    ntype = settings.NOTIFICATION_TYPES.task_rejected
    model = 'task.task'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: Text about task posted.

        """
        user_id = self.notification.user_id
        owner_id = self.notification.kwargs['owner']['pk']
        title = self.notification.kwargs['notifying']['fields']['title'] # noqa
        if owner_id == user_id:
            return "Your task \"%s\" was rejected" % title
        return "Task \"%s\" was rejected" % title


class VoteAdded(_NotifyInterface):

    """ Notify about accepted a task."""

    ntype = settings.NOTIFICATION_TYPES.vote_added
    model = 'task.task'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: A text

        """
        if notifying is None:
            notifying = self.notification.notifying
        owner_id = self.notification.kwargs['owner']['pk']
        user_id = self.notification.user_id
        prefix = ''
        if owner_id == user_id:
            prefix = 'your '

        votes = notifying.vote_set.select_related('voter').exclude(
            voter_id=user_id).order_by('-time_voted')
        first_names = list(v.voter.first_name for v in votes)

        title = self.notification.kwargs['notifying']['fields']['title']
        return "%s voted on %stask \"%s\"" % \
               (list_string_join(first_names), prefix, title)


class VoteUpdated(_NotifyInterface):

    """ Notify about accepted a task."""

    ntype = settings.NOTIFICATION_TYPES.vote_updated
    model = 'task.task'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: A text

        """
        owner_id = self.notification.kwargs['owner']['pk']
        user_id = self.notification.user_id
        prefix = ''
        if owner_id == user_id:
            prefix = 'your '
        title = self.notification.kwargs['notifying']['fields']['title']
        return "%s updated a vote on %stask \"%s\"" % (
            self.notification.kwargs['voter_first_name'], prefix, title)
