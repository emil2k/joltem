from django.db import models
from django.contrib.auth.models import User
from project.models import Project
from solution.models import Solution
from joltem.settings import MAIN_DIR

class Repository(models.Model):
    """
    Git repository
    """
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    project = models.ForeignKey(Project)

    @property
    def full_name(self):
        """
        Full name of repository, i.e. joltem/web
        """
        return "%s/%s" % (self.project.name.lower(), self.name)


    @property
    def absolute_path(self):
        """
        Absolute path to repository
        """
        return "%sgit/repositories/%s.git" % (MAIN_DIR, self.full_name)

    class Meta:
        unique_together = ("name","project")

    def __unicode__(self):
        return self.full_name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.pk:
            from pygit2 import init_repository
            init_repository(self.absolute_path, bare=True)
            # Give git group write permissions to repository
            import subprocess
            subprocess.call(['chmod', '-R', 'g+rwX', self.absolute_path])
            # Add symbolic link to gitolite update hook, otherwise write permissions won't work
            subprocess.call(['ln', '-s', '%sgit/gitolite/gitolite-update' % MAIN_DIR, '%s/hooks/update' % self.absolute_path])
            # TODO update permissions somewhere
            # TODO add custom update hook for adding commits to database
        super(Repository, self).save(force_insert, force_update, using, update_fields)

    def delete(self, using=None):
        from shutil import rmtree
        rmtree(self.absolute_path)
        super(Repository, self).delete(using)


class Branch(models.Model):
    """
    Git branch, created by a task branch
    """
    reference = models.CharField(max_length=200)
    #Relations
    repository = models.ForeignKey(Repository)
    solution = models.ForeignKey(Solution, null=True, blank=True)

    def __unicode__(self):
        return self.reference


class Authentication(models.Model):
    """
    A public authentication key for gitolite
    """
    key = models.TextField()
    # Relations
    user = models.ForeignKey(User)

    def __unicode__(self):
        return str(self.id)