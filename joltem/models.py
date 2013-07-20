from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    gravatar_email = models.CharField(max_length=200, null=True,blank=True)
    gravatar_hash = models.CharField(max_length=200, null=True,blank=True)
    # Relations
    user = models.OneToOneField(User, related_name="profile")

    @property
    def impact(self):
        # TODO this should later be switched to project specific impact, but it is fine for now as there is only one project
        impact = 0
        # The admins of the project start with an impact of 1, for weighted voting to be effective # TODO hackish missing project parameter, depends on fact that there is only one project
        if self.user.project_set.count() > 0:
            impact = 1
        # Impact from solutions
        for solution in self.user.solution_set.filter():
            # A solutions weighted acceptance must be higher than 90% to count towards impact
            if solution.acceptance < 90:
                continue
            if solution.impact:
                impact += solution.impact
        # Impact from review comments
        for comment in self.user.comment_set.filter():
            if comment.impact:
                impact += comment.impact
        return impact

    @property
    def completed(self):
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


class Invite(models.Model):
    '''
    A way to send out invitations and track invitations for developers in beta program
    '''
    invite_code = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    personal_message = models.TextField()
    is_sent = models.BooleanField(default=False)  # whether user was contacted
    is_clicked = models.BooleanField(default=False)  # whether email link was clicked or not
    is_signed_up = models.BooleanField(default=False)  # whether user signed up
    user = models.ForeignKey(User, null=True, blank=True)  # if the user registered, the associated user
    from datetime import datetime
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