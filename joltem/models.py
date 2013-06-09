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
        impact = 0 # the person who starts the project is awarded with an impact of 1 from which all other users impact will stem
        for solution in self.user.solution_set.filter(is_accepted=True, is_completed=True):
            impact += solution.impact
        return impact

    @property
    def completed(self):
        return self.user.solution_set.filter(is_completed=True).count()