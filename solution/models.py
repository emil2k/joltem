from django.db import models
from django.contrib.auth.models import User
from task.models import Task


class Solution(models.Model):
    """
    A single task can be worked on by multiple groups at the same time, in different branches for variation.
    """
    description = models.TextField()
    # Relations
    task = models.ForeignKey(Task)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return str(self.id)