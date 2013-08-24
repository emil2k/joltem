from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic, models as content_type_models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

import logging
logger = logging.getLogger('django')


# User profile related

class Profile(models.Model):
    gravatar_email = models.CharField(max_length=200, null=True, blank=True)
    gravatar_hash = models.CharField(max_length=200, null=True, blank=True)
    impact = models.BigIntegerField(default=0)
    completed = models.IntegerField(default=0)
    # Relations
    user = models.OneToOneField(User, related_name="profile")

    def update(self):
        """
        Update user stats
        """
        self.impact = self.get_impact()
        self.completed = self.get_completed()
        return self  # to chain calls

    def get_impact(self):
        impact = 0
        for project_impact in self.user.impact_set.all():
            if project_impact and project_impact.impact:
                impact += project_impact.impact
        return impact

    def get_completed(self):
        return self.user.solution_set.filter(is_completed=True).count()

    def set_gravatar_email(self, gravatar_email):
        """
        Set gravatar email and hash, checks if changed from old
        return boolean whether changed value or not
        """
        if self.gravatar_email != gravatar_email:
            import hashlib
            self.gravatar_email = gravatar_email
            self.gravatar_hash = hashlib.md5(gravatar_email).hexdigest()
            return True
        return False

@receiver(post_save, sender=User)
def create_profile(sender, **kw):
    """
    Create user profile when user created
    """
    user = kw["instance"]
    logger.info("CREATE PROFILE for %s" % user.username)
    if kw["created"]:
        profile = Profile(user=user)
        profile.update().save()

@receiver([post_save, post_delete], sender='project.Impact')
def update_from_project_impact(sender, **kwargs):
    project_impact = kwargs.get('instance')
    logger.info("UPDATE USER STATS from project impact : %s : %d for %s" % (sender, project_impact.project.id, project_impact.user.username))
    if project_impact:
        project_impact.user.get_profile().update().save()


# Invite related

class Invite(models.Model):
    '''
    A way to send out invitations and track invitations for developers in beta program
    '''
    invite_code = models.CharField(max_length=200, unique=True)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    personal_note = models.TextField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)  # whether user was contacted
    is_clicked = models.BooleanField(default=False)  # whether email link was clicked or not
    is_signed_up = models.BooleanField(default=False)  # whether user signed up
    user = models.ForeignKey(User, null=True, blank=True)  # if the user registered, the associated user
    time_sent = models.DateTimeField(null=True, blank=True)
    time_clicked = models.DateTimeField(null=True, blank=True)
    time_signed_up = models.DateTimeField(null=True, blank=True)
    # Various contact methods and profiles
    email = models.CharField(max_length=200, null=True, blank=True)
    twitter = models.CharField(max_length=200, null=True, blank=True)
    facebook = models.CharField(max_length=200, null=True, blank=True)
    stackoverflow = models.CharField(max_length=200, null=True, blank=True)  # full url
    personal_site = models.CharField(max_length=200, null=True, blank=True)

    @classmethod
    def is_valid(cls, invite_code):
        """
        Check if invite code is valid, if valid returns Invite object and False if not
        If already return False
        """
        try:
            invite = cls.objects.get(invite_code=invite_code)
            return False if invite.is_signed_up else invite
        except cls.DoesNotExist:
            return False

    @property
    def full_name(self):
        return "%s %s" % (self.first_name, self.last_name)


# Votes related

class Vote(models.Model):
    """
    Vote
    """
    voter_impact = models.BigIntegerField()  # at time of vote
    is_accepted = models.BooleanField(default=False)
    magnitude = models.SmallIntegerField(null=True, blank=True)  # represents n in 10^n for the vote, n=1 for satisfactory, n=2 for one star and so on ...
    time_voted = models.DateTimeField(default=timezone.now)
    # Relations
    voter = models.ForeignKey(User)
    # Generic relations
    voteable_type = models.ForeignKey(content_type_models.ContentType)
    voteable_id = models.PositiveIntegerField()
    voteable = generic.GenericForeignKey('voteable_type', 'voteable_id')

    MAXIMUM_MAGNITUDE = 5  # the maximum magnitude for a vote

    def __unicode__(self):
        return str(self.id)

    @property
    def is_rejected(self):
        return not self.is_accepted


class Voteable(models.Model):
    """
    Abstract, an object that can be voted on for impact determination
    """
    impact = models.BigIntegerField(null=True, blank=True)
    acceptance = models.SmallIntegerField(null=True, blank=True)  # impact-weighted percentage of acceptance
    # Relations
    project = models.ForeignKey('project.Project')
    user = models.ForeignKey(User)
    # Generic relations
    vote_set = generic.GenericRelation('joltem.Vote', content_type_field='voteable_type', object_id_field='voteable_id')

    class Meta:
        abstract = True

    def get_acceptance(self):
        """
        Impact-weighted percentage of acceptance amongst reviewers
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
            return int(round(100 * float(weighted_sum)/impact_sum))

    def get_impact(self):
        """
        Calculate impact, analogous to value of contribution
        """
        impact_sum = 0
        weighted_sum = 0
        for vote in self.vote_set.all():
            logger.debug("VOTE : accepted : %s : valid : %s : mag : %d : imp : %d" % (vote.is_accepted, self.is_vote_valid(vote), vote.magnitude, vote.voter_impact))
            if not self.is_vote_valid(vote):
                logger.info("VOTE : not valid")
                continue
            elif vote.is_accepted:
                weighted_sum += vote.voter_impact * self.get_vote_value(vote)
                logger.debug("VOTE : accepted add to weighted sum : %d" % weighted_sum)
            impact_sum += vote.voter_impact
            logger.debug("VOTE : added to impact sum : %d" % impact_sum)
        if impact_sum == 0:
            logger.debug("VOTE : impact sum == 0 : %d" % impact_sum)
            return None
        logger.info("VOTE : return impact : %d / %s" % (weighted_sum, float(impact_sum)))
        logger.info("VOTE : return impact : %s" % int(round(weighted_sum / float(impact_sum))))
        return int(round(weighted_sum / float(impact_sum)))

    def get_impact_distribution(self):
        """
        Impact distribution based on magnitude, with 0 representing a rejected vote
        """
        d = [0] * (1 + Vote.MAXIMUM_MAGNITUDE)
        for vote in self.vote_set.all():
            d[vote.magnitude] += vote.voter_impact
        return d

    def get_impact_integrals(self):
        """
        Calculate impact integrals (integration of the impact distribution from the given magnitude
        to the maximum magnitude) for each magnitude returns a list
        """
        stop = 1 + Vote.MAXIMUM_MAGNITUDE
        d = self.get_impact_distribution()
        ii = [0] * stop
        for magnitude in range(stop):
            # Integrate distribution
            for x in range(magnitude, stop):
                ii[magnitude] += d[x]
        return ii

    def get_impact_integrals_excluding_vote(self, vote):
        """
        Calculate impact integrals, excluding the specified vote
        """
        ii = self.get_impact_integrals()
        for x in range(1 + vote.magnitude):
            ii[x] -= vote.voter_impact
        return ii

    def is_vote_valid(self, vote):
        """
        Determines whether vote should be counted or not
        OVERRIDE in EXTENDING CLASS
        """
        return True

    """
    Thought process ...
    If vote is less than one standard deviation above of the actual magnitude,
    a minimum of 15.9% of the rest of distribution would be between it and the maximum.

    If there is no support at that magnitude it goes down a level to the minimum of 1
    for an accepted vote
    TODO should this go the other way too?
    """
    MAGNITUDE_THRESHOLD = 0.159  # minimum supporting impact integral

    def get_vote_value(self, vote):
        """
        Determines vote value based on the impact distribution of the other votes
        Assumes vote is accepted, so magnitude is greater than 0
        """
        assert vote.magnitude > 0
        logger.debug("GET VOTE VALUE : %d : %d" % (vote.magnitude, vote.voter_impact))
        excluding_total = sum(self.get_impact_distribution()) - vote.voter_impact
        ie = self.get_impact_integrals_excluding_vote(vote)
        if excluding_total > 0:
            for magnitude in reversed(range(1, 1 + vote.magnitude)):
                excluding_integral = ie[magnitude]
                p = float(excluding_integral) / excluding_total
                logger.debug("** %d : %.3f : %d" % (magnitude, p, excluding_integral))
                if p > Voteable.MAGNITUDE_THRESHOLD:
                    return pow(10, magnitude)
        logger.info("** VOTE : defaulted to 10")
        return 10  # default

@receiver([post_save, post_delete], sender='joltem.Vote')
def update_metrics(sender, **kwargs):
    """
    Update vote metrics (acceptance and impact) and save to DB
    """
    vote = kwargs.get('instance')
    logger.info("UPDATE METRICS from vote : %s" % vote.magnitude)
    if vote and vote.voteable:
        voteable = vote.voteable
        voteable.acceptance = voteable.get_acceptance()
        voteable.impact = voteable.get_impact()
        voteable.save()


# Comment related

class Comment(Voteable):
    """
    Comments in a solution review
    """
    # todo make tests for impact effects when voting on comments
    comment = models.TextField(null=True, blank=True)
    time_commented = models.DateTimeField(default=timezone.now)
    # Generic relations
    commentable_type = models.ForeignKey(content_type_models.ContentType)
    commentable_id = models.PositiveIntegerField()
    commentable = generic.GenericForeignKey('commentable_type', 'commentable_id')

    def __unicode__(self):
        return str(self.comment)


class Commentable(models.Model):
    """
    Abstract, an object that can be commented on
    """
    # Generic relations
    comment_set = generic.GenericRelation('joltem.Comment', content_type_field='commentable_type', object_id_field='commentable_id')

    class Meta:
        abstract = True
