""" Git related modules. """
import os

from django.db import models
from django.conf import settings

from twisted.conch.ssh.keys import Key, BadKeyError

from project.models import Project

import logging
logger = logging.getLogger('joltem')

REPOSITORIES_DIRECTORY = os.path.join(settings.PROJECT_ROOT,
                                      'gateway/repositories')


class Repository(models.Model):

    """ Git repository. """

    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    is_hidden = models.BooleanField(default=False)
    # Relations
    project = models.ForeignKey(Project)

    @property
    def absolute_path(self):
        """ Absolute path to repository.

        :return str: Path to repository

        """

        return "%s/%d.git" % (REPOSITORIES_DIRECTORY, self.id)

    def load_pygit_object(self):
        """ Load pygit2 repository object for this repository.

        :return PyGitRepository:

        """
        from pygit2 import Repository as PyGitRepository
        return PyGitRepository(self.absolute_path)

    def __unicode__(self):
        return self.name

    def save(
            self, force_insert=False, force_update=False, using=None,
            update_fields=None):
        """ Save model and init git repository.

        :return Model: A saved instance

        """
        new = False if self.pk else True
        obj = super(Repository, self).save(
            force_insert, force_update, using, update_fields)
        if new:
            from pygit2 import init_repository
            # Initiate bare repository on server
            init_repository(self.absolute_path, bare=True)
        return obj

    def delete(self, using=None):
        """ Delete repository from disk.

        NOTE: Should be backup.

        """
        from shutil import rmtree
        rmtree(self.absolute_path)

        super(Repository, self).delete(using)


class Authentication(models.Model):

    """ A public authentication key for SSH. """

    name = models.CharField(max_length=200)
    key = models.TextField()  # open ssh representation of public rsa key
    fingerprint = models.CharField(max_length=47)
    # Relations
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    @classmethod
    def load_key(cls, data):
        """ Attempt to parse data to check if it is a valid public ssh rsa key.

        :return: Returns an instance of a twisted Key object
        :raise: BadKeyError.

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
        """ Key body.

        :return blob:

        """
        key = Authentication.load_key(self.key)
        return key.blob()

    @blob.setter
    def blob(self, value):
        """ Load key. """

        key = Authentication.load_key(value)
        self.key = key.toString('OPENSSH')
        self.fingerprint = key.fingerprint()
