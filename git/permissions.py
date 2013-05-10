#!/usr/bin/env python

"""
A quick script to generate gitolite configuration with appropriate permissions
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "joltem.settings")

from git.models import Repository, Branch, Permission
from joltem.models import User

# Find file paths
gitolite_admin_directory = os.path.dirname(os.path.realpath(__file__))+"/gitolite/gitolite-admin/"
gitolite_conf_file_path = gitolite_admin_directory+"conf/gitolite.conf"

with open(gitolite_conf_file_path, 'w') as f:
    f.write("#***************************\n")
    f.write("# Generated by Joltem\n")
    f.write("#***************************\n")
    repos = Repository.objects.all()
    for repo in repos:
        # Repository permissions
        f.write("repo\t%s" % repo.path)
        repo_permissions = repo.permission_set.filter(branch=None)
        for repo_permission in repo_permissions:
            f.write("\t%s\t=\t%s\n" % (repo_permission, repo_permission.user.username))
        # Branch permissions
        f.write("# Branch permissions\n")
        branches = repo.branch_set.all()
        for branch in branches:
            branch_permissions = branch.permission_set.all()
            for branch_permission in branch_permissions:
                f.write("\t%s\t^refs/heads/%s$\t=\t%s\n" % (branch_permission, branch_permission.branch.reference, branch_permission.user.username))


print "\n*** Wrote configuration file to %s, is closed : %s.\n" % (gitolite_conf_file_path, f.closed)
# Output config file to STDOUT
from subprocess import call
call("cat %s" % gitolite_conf_file_path, shell=True)
print "\n*** Commit permission changes\n."
call("git --git-dir=%s.git --work-tree=%s commit -v -am 'Permission changes.'" % (gitolite_admin_directory, gitolite_admin_directory), shell=True)
print "\n*** Push permission changes.\n"
call("git --git-dir=%s.git --work-tree=%s push -v" % (gitolite_admin_directory, gitolite_admin_directory), shell=True)
