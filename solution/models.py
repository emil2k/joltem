from django.db import models
from django.contrib.auth.models import User
from task.models import Task


class Solution(models.Model):
    """
    A single task can be worked on by multiple groups at the same time, in different branches.

    Example :
    task/743/1 - assigned to Jill, working with Bill
    task/743/2 - assigned to Jacob, working with Matt and Carol
    ...
    """
    # Relations
    task = models.ForeignKey(Task)
    assignees = models.ManyToManyField(User)

    def __unicode__(self):
        return str(self.id)