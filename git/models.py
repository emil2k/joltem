from django.db import models
from django.contrib.auth.models import User

from twisted.conch.ssh.keys import Key, BadKeyError

from project.models import Project
from joltem.settings import MAIN_DIR

import logging
logger = logging.getLogger('joltem')

REPOSITORIES_DIRECTORY = '%sgateway/repositories' % MAIN_DIR


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
    def absolute_path(self):
        """
        Absolute path to repository
        """
        return "%s/%d.git" % (REPOSITORIES_DIRECTORY, self.id)

    def load_pygit_object(self):
        """
        Loads pygit2 repository object for this repository
        """
        from pygit2 import Repository as PyGitRepository
        return PyGitRepository(self.absolute_path)

    def __unicode__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        new = False if self.pk else True
        super(Repository, self).save(force_insert, force_update, using, update_fields)
        if new:
            from pygit2 import init_repository
            # Initiate bare repository on server
            init_repository(self.absolute_path, bare=True)

    def delete(self, using=None):
        super(Repository, self).delete(using)
        from shutil import rmtree
        rmtree(self.absolute_path)


class Authentication(models.Model):
    """
    A public authentication key for SSH
    """
    name = models.CharField(max_length=200)
    key = models.TextField()  # open ssh representation of public rsa key
    fingerprint = models.CharField(max_length=47)
    # Relations
    user = models.ForeignKey(User)

    @classmethod
    def load_key(cls, data):
        """
        Attempts to parse data to check if it is a valid public ssh rsa key.
        Returns an instance of a twisted Key object or raises BadKeyError.

        Keyword argument:
        blob -- data to parse as rsa public key

        """
        key = Key.fromString(data)
        if not key.sshType() == 'ssh-rsa':
            raise BadKeyError("No a rsa key.")
        elif not key.isPublic():
            raise BadKeyError("Not a public key.")
        else:
            return key

    def __unicode__(self):
        return self.name

    @property
    def blob(self):
        key = Authentication.load_key(self.key)
        return key.blob()

    @blob.setter
    def blob(self, value):
        key = Authentication.load_key(value)
        self.key = key.toString('OPENSSH')
        self.fingerprint = key.fingerprint()
