from django.db import models
from django.contrib.auth.models import User
from task.models import Task

from datetime import datetime


class Solution(models.Model):
    """
    A single task can be worked on by multiple groups at the same time, in different branches for variation.
    """
    description = models.TextField()
    # NOTE : No parenthesis on datetime.now because I'm passing the function not the current value
    time_posted = models.DateTimeField(default=datetime.now)
    time_edited = models.DateTimeField(null=True, blank=True)
    # Relations
    task = models.ForeignKey(Task)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return str(self.id)