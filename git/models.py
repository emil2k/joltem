from django.db import models
from django.contrib.auth.models import User
from joltem.models import Project, TaskBranch


class Repository(models.Model):
    """
    Git repository
    """
    path = models.CharField(max_length=200)  # TODO make unique
    # Relations
    project = models.ForeignKey(Project)

    def __unicode__(self):
        return self.path


class Branch(models.Model):
    """
    Git branch, created by a task branch
    """
    reference = models.CharField(max_length=200)
    #Relations
    repository = models.ForeignKey(Repository)
    task_branch = models.ForeignKey(TaskBranch, null=True, blank=True)

    def __unicode__(self):
        return self.reference


# TODO deprecated remove
class Permission(models.Model):
    """
    Gitolite permissions for a branch and user
    """
    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    # Relations
    user = models.ForeignKey(User)
    repository = models.ForeignKey(Repository)
    branch = models.ForeignKey(Branch, null=True, blank=True)

    def __unicode__(self):
        permission = ""
        if self.can_read:
            permission += "R"
        if self.can_write:
            permission += "W"
        return permission


class Authentication(models.Model):
    """
    A public authentication key for gitolite
    """
    key = models.TextField()
    # Relations
    user = models.ForeignKey(User)

    def __unicode__(self):
        return str(self.id)