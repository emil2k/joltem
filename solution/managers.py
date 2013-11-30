""" Custom manager for Solution model. """

from django.db.models.query import QuerySet


class SolutionQuerySet(QuerySet):

    """ Im really dont known what the goal of the Manager.

    Because implicit better explicit. And not so much economy here::

        Solution.objects.completed()

        # VS

        Solution.objects.filter(is_completed=True, is_closed=False)

    """

    def reviewed_by_user(self, user):
        """ Return solutions which have been voted by given user.

        :return QuerySet:

        """
        return self.filter(vote_set__voter_id=user.id)

    def need_review_from_user(self, user):
        """ Return solutions which have not been voted by given user yet.

        User's solutions are excluded.

        :return QuerySet:

        """
        return self.filter(is_completed=True, is_closed=False) \
                   .exclude(vote_set__voter_id=user.id) \
                   .exclude(owner_id=user.id)

    def incomplete(self):
        """ Return incomplete solutions.

        :return QuerySet:

        """
        return self.filter(is_completed=False, is_closed=False)

    def incomplete_by_user(self, user):
        """ Return user's incomplete solutions.

        :return QuerySet:

        """
        return self.incomplete().filter(owner_id=user.id)

    def completed(self):
        """ Return completed but still not closed solutions.

        :return QuerySet:

        """
        return self.filter(is_completed=True, is_closed=False)

    def completed_by_user(self, user):
        """ Return user's completed but still not closed solutions.

        :return QuerySet:

        """
        return self.completed().filter(owner_id=user.id)
