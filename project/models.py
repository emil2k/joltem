from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    users = models.ManyToManyField(User)

    def __unicode__(self):
        return self.name