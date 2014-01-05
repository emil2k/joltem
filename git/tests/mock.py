from datetime import datetime

import pygit2
import uuid

from git.utils import get_branch_reference


def get_mock_signature(name, email=None):
    """ Get a mock signature object from pygit2.

    Returns a pygit2 Signature object.

    """
    email = '%s@gmail.com' % name if email is None else email
    return pygit2.Signature(name, email)


def get_mock_commit(repository, tree_oid, signature,
                    reference, message, parents):
    """ Make a mock commit to the given repository, returns commit Oid. """
    commit_oid = repository.create_commit(
        reference,              # reference to update
        signature,              # author
        signature,              # committer
        message,                # message
        tree_oid,               # commit tree, representing file structure
        parents                 # commit parents
    )
    return commit_oid


def put_mock_file(name, data, repository, tree=None):
    """ Put a mock file into a tree.

    If tree not passed creates a tree.
    Emulate addition or update of files, returns new tree Oid.

    """
    blob_oid = repository.create_blob(data)
    # Put blob into tree
    builder = repository.TreeBuilder(tree) if tree is not None \
        else repository.TreeBuilder()
    builder.insert(name, blob_oid, pygit2.GIT_FILEMODE_BLOB)
    # Create tree
    tree_oid = builder.write()
    return tree_oid


def mock_commits(number, pygit_repository, signature,
                 branch_name, initial_parents):
    """ Generator for sequential commits. """
    commit_oid = None
    for _ in range(number):
        parents = [commit_oid] if commit_oid else initial_parents
        commit_oid = make_mock_commit(pygit_repository, signature,
                                      branch_name, parents)
        yield commit_oid


def make_mock_commit(pygit_repository, signature, branch_name, parents):
    """ Make a mock commit and returns its commit Oid. """
    datetime_string = datetime.now().strftime("%X on %x")
    tree_oid = put_mock_file(
        "test.txt", "Line added at %s.\n%s" % (datetime_string, uuid.uuid4()),
        pygit_repository)
    commit_oid = get_mock_commit(
        pygit_repository,
        tree_oid,
        signature,
        get_branch_reference(branch_name),
        "Mock commit to `%s` at %s." % (branch_name, datetime_string),
        parents
    )
    return commit_oid
