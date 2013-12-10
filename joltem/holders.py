""" Rare using functionality. """


class CommentHolder:

    """ Should have a docstring. """



    def __init__(self, comment, user):
        self.comment = comment
        self.url = comment.get_comment_url()
        self.vote = None
        self.accept_votes = []
        self.reject_votes = []
        self.vote_count = 0
        for v in comment.vote_set.all():
            self.vote_count += 1
            if v.voter_id == user.id:
                self.vote = v
            if v.is_accepted:
                self.accept_votes.append(v)
            else:
                self.reject_votes.append(v)
        self.is_author = user.id == comment.owner_id

    @classmethod
    def get_comments(cls, query_set, user):
        """ Get all comments in queryset and determine the passed user's vote.

        :return list:

        """
        return [CommentHolder(comment, user) for comment in query_set]


class NotificationHolder:

    """ Should have a docstring. """

    def __init__(self, notification):
        self.notification = notification
        self.notifying = notification.notifying
        self.text = self.notifying.get_notification_text(notification)
        self.url = self.notifying.get_notification_url(notification)

    @classmethod
    def get_notifications(cls, user):
        """ Get all notifications (in holders) for the passed user.

        :return list:

        """
        return [
            NotificationHolder(notification)
            for notification in user.notification_set.all().order_by(
                "-time_notified")]
