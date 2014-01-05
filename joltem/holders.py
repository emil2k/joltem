""" Rare using functionality. """


class CommentHolder:

    """ Should have a docstring. """

    def __init__(self, comment, user):
        self.comment = comment
        self.url = comment.get_comment_url()
        self.is_author = user.id == comment.owner_id

    @classmethod
    def get_comments(cls, query_set, user):
        """ Get all comments in queryset and determine the passed user's vote.

        :return list:

        """
        return [CommentHolder(comment, user) for comment in query_set]
