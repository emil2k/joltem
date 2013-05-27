from django.db import models
from django.contrib.auth.models import User
from project.models import Project
from solution.models import Solution


class Repository(models.Model):
    """
    Git repository
    """
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    # Relations
    project = models.ForeignKey(Project)

    @property
    def path(self):
        """
        Relative path to repository from the repositories folder, without ending .git
        """
        return "%s/%s" % (self.project.name.lower(), self.name)


    @property
    def path_in_project(self):
        """
        Relative path to repository from the project folder, with ending .git
        """
        return "git/repositories/%s.git" % self.path

    class Meta:
        unique_together = ("name","project")

    def __unicode__(self):
        return self.path

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.pk:
            from pygit2 import init_repository
            init_repository(self.path_in_project, bare=True)
            # Give git group write permissions to repository
            import subprocess
            subprocess.call(['chmod', '-R', 'g+w', self.path_in_project])
        super(Repository, self).save(force_insert, force_update, using, update_fields)

    def delete(self, using=None):
        from shutil import rmtree
        rmtree(self.path_in_project)
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