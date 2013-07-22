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
    is_hidden = models.BooleanField(default=False)
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
        new = False if self.pk else True
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


class Authentication(models.Model):
    """
    A public authentication key for SSH
    """
    name = models.CharField(max_length=200)
    key = models.TextField()
    # Relations
    user = models.ForeignKey(User)

    def __unicode__(self):
        return str(self.id)

    @classmethod
    def update(cls):
        from git.gitolite.permissions import update_permissions
        from git.gitolite.keys import update_keys
        # Update gitolite permissions to include new user, must be done after actually saved to DB
        update_permissions()
        # Update gitolite keys to include new user
        update_keys()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        new = False if self.pk else True
        super(Authentication, self).save(force_insert, force_update, using, update_fields)
        if new:
            Authentication.update()

    def delete(self, using=None):
        super(Authentication, self).delete(using)
        Authentication.update()