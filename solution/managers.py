# coding: utf-8
from django.db.models.query import QuerySet


class SolutionQuerySet(QuerySet):

    def reviewed_by_user(self, user):
        """Returns solutions which have been voted by given user."""
        return self.filter(vote_set__voter_id=user.id)

    def need_review_from_user(self, user):
        """Returns solutions which have not been voted by given user yet.

        User's solutions are excluded.

        """
        return self.filter(is_completed=True, is_closed=False) \
                   .exclude(vote_set__voter_id=user.id) \
                   .exclude(owner_id=user.id)

    def incomplete(self):
        """Returns incomplete solutions."""
        return self.filter(is_completed=False, is_closed=False)

    def incomplete_by_user(self, user):
        """Returns user's incomplete solutions."""
        return self.incomplete().filter(owner_id=user.id)

    def completed(self):
        """Returns completed but still not closed solutions."""
        return self.filter(is_completed=True, is_closed=False)

    def completed_by_user(self, user):
        """Returns user's completed but still not closed solutions."""
        return self.completed().filter(owner_id=user.id)
