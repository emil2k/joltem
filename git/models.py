from django.db import models
from django.contrib.auth.models import User
from joltem.models import Project, TaskBranch


class Repository(models.Model):
    """
    Git repository
    """
    path = models.CharField(max_length=200)
    # Relations
    project = models.ForeignKey(Project)


class Branch(models.Model):
    """
    Git branch, created by a task branch
    """
    reference = models.CharField(max_length=200)
    #Relations
    repository = models.ForeignKey(Repository)
    task_branch = models.ForeignKey(TaskBranch, null=True)


class Permission(models.Model):
    """
    Gitolite permissions for a branch and user
    """
    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    # Relations
    user = models.ForeignKey(User)
    branch = models.ForeignKey(Branch)