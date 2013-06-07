from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    gravatar_email = models.CharField(max_length=200, null=True,blank=True)
    gravatar_hash = models.CharField(max_length=200, null=True,blank=True)
    # Relations
    user = models.OneToOneField(User, related_name="profile")

    @property
    def impact(self):
        impact = 1  # default to 1 to prevent divide by zero problems
        for solution in self.user.solution_set.filter(is_accepted=True, is_completed=True):
            impact += solution.impact
        return impact

    @property
    def completed(self):
        return self.user.solution_set.filter(is_completion_accepted=True).count()