from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    users = models.ManyToManyField(User)


# TODO move to git app
class Repository(models.Model):
    """
    A Git repository
    """
    path = models.CharField(max_length=200)
    # Relations
    project = models.ForeignKey(Project)


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    parent = models.ForeignKey('self', null=True)
    project = models.ForeignKey(Project)


class TaskBranch(models.Model):
    """
    A single task can be worked on by multiple groups at the same time, in different branches.
    Example :
    task/743/a - assigned to Jill, working with Bill
    task/743/b - assigned to Jacob, working with Matt and Carol
    ...
    """
    # Relations
    task = models.ForeignKey(Task)

# TODO move to git app
class Branch(models.Model):
    """
    A Git branch, created by a task branch
    """
    reference = models.CharField(max_length=200)
    #Relations
    repository = models.ForeignKey(Repository)
    task_branch = models.ForeignKey(TaskBranch, null=True)


class Permission(models.Model):
    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    # Relations
    user = models.ForeignKey(User)
    branch = models.ForeignKey(Branch)
