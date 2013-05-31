from django.db import models
from django.contrib.auth.models import User
from project.models import Project
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
            new = True
        super(Repository, self).save(force_insert, force_update, using, update_fields)
        if new:
            import subprocess
            from pygit2 import init_repository
            from git.gitolite.permissions import update_permissions
            # Initiate bare repository on server
            init_repository(self.absolute_path, bare=True)
            # Give git group necessary permissions to repository
            subprocess.call(['chmod', '-R', 'g+rwX', self.absolute_path])
            # Add symbolic link to gitolite update hook, otherwise gitolite write permissions enforcement won't work
            subprocess.call(['ln', '-s', '%sgit/gitolite/gitolite-update' % MAIN_DIR, '%s/hooks/update' % self.absolute_path])
            # Update gitolite permissions to include new repository, must be done after actually saved to DB
            update_permissions()

    def delete(self, using=None):
        super(Repository, self).delete(using)
        from shutil import rmtree
        from git.gitolite.permissions import update_permissions
        rmtree(self.absolute_path)
        update_permissions()


class Commit(models.Model):
    sha = models.CharField(max_length=40, unique=True)
    message = models.TextField()
    message_encoding = models.CharField(max_length=200, null=True, blank=True)
    commit_time = models.DateTimeField()
    # Relations
    repository = models.ForeignKey(Repository)
    parents = models.ManyToManyField('self')
    # TODO remove tie with Signature and just credit to a registered user
    # just store emails for now
    author = models.CharField(max_length=200)
    committer = models.CharField(max_length=200)

    def __unicode__(self):
        return self.sha


class Authentication(models.Model):
    """
    A public authentication key for gitolite
    """
    key = models.TextField()
    # Relations
    user = models.ForeignKey(User)

    def __unicode__(self):
        return str(self.id)