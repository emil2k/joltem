
class CommentHolder:
    def __init__(self, comment, user):
        from joltem.models import Vote
        self.comment = comment
        try:
            self.vote = comment.vote_set.get(voter_id=user.id)
        except Vote.DoesNotExist:
            self.vote = None
        self.is_author = user.id == comment.user.id
        self.vote_count = comment.vote_set.count()

    @classmethod
    def get_comments(cls, query_set, user):
        return [CommentHolder(comment, user) for comment in query_set]