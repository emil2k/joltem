""" Template holders for Joltem app. """


class CommentHolder:

    """ Holder for comments. """

    def __init__(self, comment, user):
        self.comment = comment
        self.url = comment.get_absolute_url()
        self.is_author = user.id == comment.owner_id

    @classmethod
    def get_comments(cls, query_set, user):
        """ Get all comments in queryset and determine the passed user's vote.

        :return list:

        """
        return [CommentHolder(comment, user) for comment in query_set]
