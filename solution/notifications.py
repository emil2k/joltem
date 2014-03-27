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
        if notifying.owner_id == user_id:
            prefix = 'your '
        return "%s commented on %ssolution \"%s\"" % (
            list_string_join(first_names), prefix, notifying.default_title)


class VoteAdded(_NotifyInterface):

    """ Notify about added a vote."""

    ntype = settings.NOTIFICATION_TYPES.vote_added
    model = 'solution.solution'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: A text

        """
        if notifying is None:
            notifying = self.notification.notifying
        first_names = notifying.get_voter_first_names(
            queryset=notifying.vote_set.select_related('voter').exclude(
                voter_id=self.notification.user_id).order_by("-time_voted")
        )
        prefix = ''
        if notifying.owner_id == self.notification.user_id:
            prefix = 'your '

        return "%s voted on %ssolution \"%s\"" % \
               (list_string_join(first_names), prefix, notifying.default_title)


class VoteUpdated(_NotifyInterface):

    """ Notify about update a vote."""

    ntype = settings.NOTIFICATION_TYPES.vote_updated
    model = 'solution.solution'

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
        try:
            return "%s updated a vote on %ssolution \"%s\"" % \
                   (self.notification.kwargs["voter_first_name"], prefix,
                    notifying.default_title)
        except KeyError:
            return "A vote was updated on %ssolution \"%s\"" % \
                   prefix, notifying.default_title


class SolutionEvaluationChanged(_NotifyInterface):

    """ Notify about change evaluation of solution."""

    ntype = settings.NOTIFICATION_TYPES.solution_evaluation_changed
    model = 'solution.solution'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: A text

        """
        if notifying is None:
            notifying = self.notification.notifying
        return "Update your vote, the evaluation of \"%s\" was changed" \
               % notifying.default_title


class SolutionMarkedComplete(_NotifyInterface):

    """ Notify about solution was marked complete."""

    ntype = settings.NOTIFICATION_TYPES.solution_marked_complete
    model = 'solution.solution'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: A text

        """
        if notifying is None:
            notifying = self.notification.notifying
        return "Solution \"%s\" was marked complete" % notifying.default_title


class SolutionMarkedClosed(_NotifyInterface):

    """ Notify that solution was marked closed."""

    ntype = settings.NOTIFICATION_TYPES.solution_marked_closed
    model = 'solution.solution'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: A text

        """
        if notifying is None:
            notifying = self.notification.notifying
        return "%s closed your solution \"%s\"" % \
               (notifying.closer.first_name, notifying.default_title)


class SolutionPosted(_NotifyInterface):

    """ Notify about solution was marked complete."""

    ntype = settings.NOTIFICATION_TYPES.solution_posted
    model = 'solution.solution'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: A text

        """
        if notifying is None:
            notifying = self.notification.notifying

        owner_name = self.notification.kwargs['owner']['fields']['first_name']

        if self.notification.kwargs["role"] == "parent_task":
            return "%s posted a solution on your task \"%s\"" % \
                   (owner_name, notifying.task.title)
        elif self.notification.kwargs["role"] == "parent_solution":
            return "%s posted a solution on your solution \"%s\"" % \
                   (owner_name, notifying.solution.default_title)
        elif self.notification.kwargs["role"] == "project_admin":
            return "%s posted a solution" % owner_name


class SolutionArchived(_NotifyInterface):

    """ Notify about solution was marked archive."""

    ntype = settings.NOTIFICATION_TYPES.solution_archived
    model = 'solution.solution'

    def get_text(self, notifying=None, user=None):
        """ Get text for current notification.

        :returns: A text

        """
        return "Solution \"%s\" was archived" % notifying.default_title
