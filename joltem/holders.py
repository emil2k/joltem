
class CommentHolder:
    def __init__(self, comment, user):
        from joltem.models import Vote
        self.comment = comment
        self.url = comment.get_comment_url()
        try:
            self.vote = comment.vote_set.get(voter_id=user.id)
        except Vote.DoesNotExist:
            self.vote = None
        self.is_author = user.id == comment.owner.id
        self.vote_count = comment.vote_set.count()

    @classmethod
    def get_comments(cls, query_set, user):
        """
        Get all comments in query set, and determine the passed user's vote on them
        """
        return [CommentHolder(comment, user) for comment in query_set]


class NotificationHolder:
    def __init__(self, notification):
        self.notification = notification
        self.notifying = notification.notifying
        self.text = self.notifying.get_notification_text(notification)
        self.url = self.notifying.get_notification_url(notification)

    @classmethod
    def get_notifications(cls, user):
        """
        Get all notifications (in holders) for the passed user
        """
        return [NotificationHolder(notification) for notification in user.notification_set.all().order_by("-time_notified")]