from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    users = models.ManyToManyField(User)

    def is_admin(self, user):
        """
        Check if user is an admin of the project
        """
        return self.users.filter(id=user.id).count() > 0

    def __unicode__(self):
        return self.name