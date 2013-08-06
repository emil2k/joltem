from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from project.models import Impact, Project

import logging
logger = logging.getLogger('django')


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
        self.save()

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
        profile.save()

@receiver([post_save, post_delete], sender=Impact)
def update_from_project_impact(sender, **kwargs):
    project_impact = kwargs.get('instance')
    logger.info("UPDATE USER STATS from project impact : %s on %s" % (project_impact.user.username, project_impact.project.name))
    if project_impact:
        project_impact.user.get_profile().update()


@receiver([post_save, post_delete], sender=Project)
def update_from_project(sender, **kwargs):
    # this is because the admins of the project start off with an impact of 1
    project = kwargs.get('instance')
    logger.info("UPDATE USER STATS from project : %s" % project.name)
    if project:
        for admin in project.admin_set.all():
            admin.get_profile().update()


class Invite(models.Model):
    '''
    A way to send out invitations and track invitations for developers in beta program
    '''
    invite_code = models.CharField(max_length=200, unique=True)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    personal_message = models.TextField()
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