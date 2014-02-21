""" Voting related models. """

from django.db import models
from django.conf import settings
from django.contrib.contenttypes import generic, models as content_type_models
from django.contrib.contenttypes.generic import ContentType
from django.utils import timezone

from .notifications import Notifying
from .generic import Owned, ProjectContext


# Votes related

class Vote(models.Model):

    """ Vote that can affect impact. """

    voter_impact = models.BigIntegerField()  # at time of vote
    is_accepted = models.BooleanField(default=False)
    time_voted = models.DateTimeField(default=timezone.now)
    # Relations
    voter = models.ForeignKey(settings.AUTH_USER_MODEL)
    # Generic relations
    voteable_type = models.ForeignKey(content_type_models.ContentType)
    voteable_id = models.PositiveIntegerField()
    voteable = generic.GenericForeignKey('voteable_type', 'voteable_id')

    MAXIMUM_MAGNITUDE = 5  # the maximum magnitude for a vote

    class Meta:
        app_label = "joltem"

    def __unicode__(self):
        return str(self.id)

    @property
    def is_rejected(self):
        """ Return boolean of whether a rejection voted. """
        return not self.is_accepted


VOTEABLE_THRESHOLD = 50  # int between 0-100


class Voteable(Notifying, Owned, ProjectContext):

    """ An abstract object, that can be voted on for impact determination.

    Impact is determined through a bargaining process where the user
    offers their work for a review along with an evaluation of the impact it
    should receive.

    Reviewers determine through simple yay or nay votes determine whether
    the work is satisfactory and whether the evaluation is fair. If impact
    weighted acceptance is above the VOTEABLE_THRESHOLD the user gets all
    the impact if it is not they get none and must adjust their work or
    evaluation and resubmit for review.

    """

    impact = models.BigIntegerField(null=True, blank=True)
    # impact-weighted percentage of acceptance
    acceptance = models.SmallIntegerField(null=True, blank=True)
    # Generic relations
    vote_set = generic.GenericRelation(
        'joltem.Vote', content_type_field='voteable_type',
        object_id_field='voteable_id')

    class Meta:
        abstract = True

    def put_vote(self, voter, is_accepted):
        """ Add or update a vote on this voteable.

        :param voter:
        :param is_accepted:

        """
        if not self.update_vote(voter, is_accepted):
            self.add_vote(voter, is_accepted)

    def add_vote(self, voter, is_accepted):
        """ Add a vote by the user. """
        vote = Vote(
            voteable=self,
            voter=voter,
            is_accepted=is_accepted,
            time_voted=timezone.now(),
            voter_impact=voter.impact
        )
        vote.save()
        self.notify_vote_added(vote)

    def update_vote(self, voter, is_accepted):
        """ Update vote by the user on this voteable.

        :param voter:
        :param is_accepted:
        :return bool: whether existing vote was found and updated.

        """
        try:
            voteable_type = ContentType.objects.get_for_model(self)
            # Attempt to load vote to update it
            vote = Vote.objects.get(
                voteable_type_id=voteable_type.id,
                voteable_id=self.id,
                voter_id=voter.id
            )
            old_vote_is_accepted = vote.is_accepted
            if old_vote_is_accepted != is_accepted:
                vote.is_accepted = is_accepted
                vote.time_voted = timezone.now()
                vote.voter_impact = voter.impact
                vote.save()
                self.notify_vote_updated(vote, old_vote_is_accepted)
            return True
        except Vote.DoesNotExist:
            return False

    def notify_vote_added(self, vote):
        """ Send out notification that vote was added. """
        for user in self.followers:
            if user == vote.voter:
                continue

            self.notify(
                user, settings.NOTIFICATION_TYPES.vote_added, True)

    def notify_vote_updated(self, vote, old_vote_is_accepted):
        """ Send out notification that vote was updated.

        Override in extending class to disable

        """
        for user in self.followers:
            if user == vote.voter:
                continue
            self.notify(
                self.owner, settings.NOTIFICATION_TYPES.vote_updated, False,
                {"voter_first_name": vote.voter.first_name})

    def iterate_voters(self, queryset=None, exclude=None):
        """ Iterate through votes and return distinct voters.

        :returns: Voters generator.

        """
        if queryset is None:
            queryset = self.vote_set.select_related('voter')

        if not exclude is None:
            queryset = queryset.exclude(**exclude)

        voter_ids = []
        for vote in queryset:
            if not vote.voter_id in voter_ids:
                voter_ids.append(vote.voter_id)
                yield vote.voter

    def get_voter_first_names(self, queryset=None, exclude=None):
        """ Return a distinct list of the voter first names.

        :return list:

        """
        return [voter.first_name for voter in
                self.iterate_voters(queryset=queryset, exclude=exclude)]

    def get_acceptance(self):
        """ Impact-weighted percentage of acceptance amongst reviewers.

        Returns a int between 0 and 100.

        """
        votes = self.vote_set.filter(voter_impact__gt=0)
        impact_sum = 0
        weighted_sum = 0
        for vote in votes:
            if not self.is_vote_valid(vote):
                continue
            elif vote.is_accepted:
                weighted_sum += vote.voter_impact
            impact_sum += vote.voter_impact
        if impact_sum == 0:
            return None
        else:
            return int(round(100 * float(weighted_sum) / impact_sum))

    def get_impact(self):
        """ Calculate impact, analogous to value of contribution.

        If the impact weighted acceptance is above the VOTEABLE_THRESHOLD
        then user gets all the impact they demanded in their evaluation
        otherwise they get none.

        :return int: value of contribution

        """
        if self.get_acceptance() > VOTEABLE_THRESHOLD:
            return self.impact

        return 0

    @staticmethod
    def is_vote_valid(vote):
        """ Return boolean of whether vote should be counted or not.

        Override in extended class, to modify behaviour.

        """
        return True

    @property
    def followers(self):
        """ Get users for notify.

        :returns: A set of voters.

        """
        return set(self.iterate_voters()).union(set([self.owner]))
