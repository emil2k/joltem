""" Custom manager for Solution model. """

from django.db.models.query import QuerySet


class SolutionQuerySet(QuerySet):

    """ Im really dont known what the goal of the Manager.

    Because implicit better explicit. And not so much economy here::

        Solution.objects.completed()

        # VS

        Solution.objects.filter(is_completed=True, is_closed=False)

    """

    def incomplete(self):
        """ Return incomplete solutions.

        :return QuerySet:

        """
        return self.filter(is_completed=False, is_closed=False)

    def completed(self):
        """ Return completed but still not closed solutions.

        :return QuerySet:

        """
        return self.filter(is_completed=True, is_closed=False)
