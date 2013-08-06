from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    name = models.CharField(max_length=200)  # this is used in the domains, must be lowercase, and only contain a-z and 0-9
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    admin_set = models.ManyToManyField(User)

    def is_admin(self, user_id):
        """
        Check if user is an admin of the project
        """
        return self.admin_set.filter(id=user_id).exists()

    def __unicode__(self):
        return self.name