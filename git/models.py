""" Git related modules. """
import logging
from django.conf import settings
from django.db import models
from model_utils.managers import PassThroughManager
from pygit2 import Repository as PyGitRepository
from twisted.conch.ssh.keys import Key, BadKeyError

from .managers import RepositoryQuerySet
from project.models import Project


logger = logging.getLogger('joltem')


class Repository(models.Model):

    """ Git repository. """

    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    is_hidden = models.BooleanField(default=False)

    time_updated = models.DateTimeField(auto_now=True)

    # Relations
    project = models.ForeignKey(Project)

    objects = PassThroughManager.for_queryset_class(RepositoryQuerySet)()

    @property
    def absolute_path(self):
        """ Absolute path to repository.

        :return str: Path to repository

        """

        return "%s/%d.git" % (settings.GATEWAY_REPOSITORIES_DIR, self.id)

    def load_pygit_object(self):
        """ Load pygit2 repository object for this repository.

        :return PyGitRepository:

        """
        try:
            return PyGitRepository(self.absolute_path)
        except KeyError:
            pass

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
    fingerprint = models.CharField(max_length=47, blank=True)

    # Relations
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    project = models.ForeignKey(Project, null=True, blank=True)

    def save(self, **kwargs):
        """ Calculate fingerprint if not exists.

        :returns: A saved instance

        """
        if not self.fingerprint:
            key = Authentication.load_key(self.key)
            self.fingerprint = key.fingerprint()

        return super(Authentication, self).save(**kwargs)

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
