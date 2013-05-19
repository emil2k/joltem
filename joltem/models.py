from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    users = models.ManyToManyField(User)

    def __unicode__(self):
        return self.name


# TODO move to task app Task and TaskBranch

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    parent = models.ForeignKey('self', null=True, blank=True)
    project = models.ForeignKey(Project)

    def __unicode__(self):
        return self.title


class TaskBranch(models.Model):
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