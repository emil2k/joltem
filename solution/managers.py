# coding: utf-8
from django.db.models.query import QuerySet


class SolutionQuerySet(QuerySet):

    def reviewed_by_user(self, user):
        """Returns solutions which have been voted by given user."""
        return self.filter(vote_set__voter=user)
