""" Another useless manager. """

from django.db.models.query import QuerySet


class RepositoryQuerySet(QuerySet):

    """ Another useless manager. """

    def visible(self):
        """ Filter repositories by status.

        :return QuerySet:

        """
        return self.filter(is_hidden=False)
