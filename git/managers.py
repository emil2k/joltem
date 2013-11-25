# coding: utf-8
from django.db.models.query import QuerySet


class RepositoryQuerySet(QuerySet):

    def visible(self):
        return self.filter(is_hidden=False)
