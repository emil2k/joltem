# coding: utf-8
from django.db.models.query import QuerySet


class SolutionQuerySet(QuerySet):

    def reviewed_by_user(self, user):
        """Returns solutions which have been voted by given user."""
        return self.filter(vote_set__voter=user)

    def need_review_from_user(self, user):
        """Returns solutions which have not been voted by given user yet.

        User's solutions are excluded.

        """
        return self.filter(is_completed=True, is_closed=False) \
                   .exclude(vote_set__voter=user) \
                   .exclude(owner_id=user.id)
