from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete

from git import receivers
from project.models import Project
from joltem.settings import MAIN_DIR

import logging
logger = logging.getLogger('joltem')

GITOLITE_REPOSITORIES_DIRECTORY = '%sgit/repositories/' % MAIN_DIR
GITOLITE_ADMIN_DIRECTORY = '%sgit/gitolite/gitolite-admin/' % MAIN_DIR
GITOLITE_KEY_DIRECTORY = '%skeydir/' % GITOLITE_ADMIN_DIRECTORY
GITOLITE_CONFIG_FILE_PATH = '%sconf/gitolite.conf' % GITOLITE_ADMIN_DIRECTORY
GITOLITE_CONFIG_PREFIX = """
#===========================
# Administration
#===========================

repo\tgitolite-admin
\tRW+\t=\tadmin

#===========================
# Repositories
#===========================

"""

post_save.connect(receivers.update_config, sender=User)
post_delete.connect(receivers.update_config, sender=User)


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
        return "%s%s.git" % (GITOLITE_REPOSITORIES_DIRECTORY, self.full_name)

    def load_pygit_object(self):
        """
        Loads pygit2 repository object for this repository
        """
        from pygit2 import Repository as PyGitRepository
        return PyGitRepository(self.absolute_path)

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
            # Initiate bare repository on server
            init_repository(self.absolute_path, bare=True)
            # Give git group necessary permissions to repository
            subprocess.call(['chmod', '-R', 'g+rwX', self.absolute_path])
            # Add symbolic link to gitolite update hook, otherwise gitolite write permissions enforcement won't work
            subprocess.call(['ln', '-sf', '%sgit/gitolite/gitolite-update' % MAIN_DIR, '%s/hooks/update' % self.absolute_path])

    def delete(self, using=None):
        super(Repository, self).delete(using)
        from shutil import rmtree
        rmtree(self.absolute_path)

post_save.connect(receivers.update_config, sender=Repository)
post_delete.connect(receivers.update_config, sender=Repository)


class Authentication(models.Model):
    """
    A public authentication key for SSH
    """
    name = models.CharField(max_length=200)
    key = models.TextField()
    # Relations
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.name

    @property
    def file_path(self):
        file_path = "%s%s@%s.pub" % (GITOLITE_KEY_DIRECTORY, self.user.username, self.id)
        logger.info("Get file key path : %s" % file_path)
        return file_path


post_save.connect(receivers.add_key, sender=Authentication)
post_delete.connect(receivers.remove_key, sender=Authentication)


# Git utility functions

def whoami():
    """
    Run the `whoami` command to find out the user running the processeses
    """
    from subprocess import Popen, PIPE
    p = Popen("whoami", shell=True, stdout=PIPE, stderr=PIPE)
    (out, error) = p.communicate()
    logger.debug("WHOAMI : " + out)
    if error:
        logger.error("WHOAMI ERROR: " + error)  # even if git command is fine, returns in stderr for some reason


def git_command(command):
    if command:
        from subprocess import Popen, PIPE
        p = Popen("git --git-dir={0}.git --work-tree={0} {1}".format(GITOLITE_ADMIN_DIRECTORY, command), shell=True, stdout=PIPE, stderr=PIPE)
        (out, error) = p.communicate()
        logger.debug(out)
        if error:
            logger.error(error)  # even if git command is fine, returns in stderr for some reason


def commit_push():
    """
    Commit and push changes
    """
    logger.debug("Commit & push")
    git_command("commit -v -am 'Keys changes.'")
    git_command("push -v origin master")
