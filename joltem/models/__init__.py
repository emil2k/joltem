from django.core.urlresolvers import reverse
import hashlib
import logging
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from taggit.managers import TaggableManager

from .notifications import Notification, Notifying  # noqa
from .votes import Vote, Voteable  # noqa
from .comments import Comment, Commentable  # noqa

from .utils import Choices, TaggedItem


logger = logging.getLogger('django')


class User(AbstractUser):

    """ Model for Joltem authenticated users.

    :param gravatar_email:
    :param gravatar_hash:
    :param impact: cumulative total impact earned, saved for caching.
    :param completed: count of completed solutions, saved for caching.
    :param notifications: count of uncleared notifications, saved for caching.
    :param can_contact: whether can send emails to user.
    :param notify_by_email: setting for frequency of delivering notification
        emails.
    :param time_notified: last time of notifying user.
    :param about: small optional bio, supports markdown.
    :param tags: skills the user has mentioned, used to match with tasks.

    """

    NOTIFY_CHOICES = Choices(
        (0, "disable"),
        (10, "immediately"),
        (20, "daily", "daily digest"),
    )

    gravatar_email = models.CharField(max_length=200, null=True, blank=True)
    gravatar_hash = models.CharField(max_length=200, null=True, blank=True)
    impact = models.BigIntegerField(default=0)
    completed = models.IntegerField(default=0)
    notifications = models.IntegerField(default=0)
    can_contact = models.BooleanField(default=True)
    notify_by_email = models.PositiveSmallIntegerField(
        default=NOTIFY_CHOICES.disable, choices=NOTIFY_CHOICES)
    time_notified = models.DateTimeField(default=timezone.now)
    about = models.TextField(blank=True)
    # Relations
    tags = TaggableManager(through=TaggedItem, blank=True)


    def update(self):
        """ Update user stats.
        """
        self.impact = self.get_impact()
        self.completed = self.get_completed()
        return self  # to chain calls

    def get_impact(self):
        impact = 0
        for project_impact in self.impact_set.all():
            if project_impact and project_impact.impact:
                impact += project_impact.impact
        return impact

    def get_completed(self):
        return self.solution_set.filter(is_completed=True).count()

    @property
    def gravatar(self):
        """ Return the gravatar image source url. """
        return 'https://secure.gravatar.com/avatar/%s' % self.gravatar_hash

    @gravatar.setter
    def gravatar(self, email):
        """ Set the gravatar hash and email properties.

        :param email: gravatar email.

        """
        self.gravatar_email = email
        self.gravatar_hash = hashlib.md5(email).hexdigest()

    @property
    def unsubscribe(self):
        """ Return an unsubscribe link for the user.

        The link is timestamped and will expire in 7 days.

        :return:

        """
        token = self.make_token()
        return reverse('unsubscribe',
                       kwargs={'username': self.username, 'token': token,})

    def make_token(self):
        """ Make timestamped token.

        :return string: token

        """
        key = TimestampSigner().sign(self.username)
        return key.split(":", 1)[1]

    def check_token(self, token):
        """ Checks that token is valid and hasn't expired.

        Expire after a week.

        :param token:
        :return boolean: whether token is valid.

        """
        try:
            key = '%s:%s' % (self.username, token)
            TimestampSigner().unsign(key, max_age=60 * 60 * 24 * 7)
        except BadSignature, SignatureExpired:
            return False
        return True