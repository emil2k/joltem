from django.test import TestCase

from git.models import Repository
from project.models import Project

from joltem.tests import TEST_LOGGER, TestCaseDebugMixin
from joltem.tests.mocking import get_mock_project, get_mock_repository

from pygit2 import Repository as PyGitRepository, Signature


# Helpers

def get_branch_reference(branch_name):
    """
    Get branch reference name from branch name
    """
    return 'refs/heads/%s' % branch_name


# Mocking helpers

def get_mock_signature(name, email=None):
    """
    Get a mock signature object from pygit2
    """
    email = '%s@gmail.com' % name if email is None else email
    return Signature(name, email)


def get_mock_commit(repository, tree_oid, signature, reference, message):
    """
    Make a mock commit to the given repository, returns commit Oid
    """
    commit_oid = repository.create_commit(
        reference,              # reference to update
        signature,              # author
        signature,              # committer
        message,                # message
        tree_oid,               # commit tree, representing file structure
        []                      # todo commit parents?
    )
    TEST_LOGGER.debug("CREATED COMMIT : %s - %s" % (commit_oid.hex, commit_oid))
    return commit_oid


def put_file_to_tree(name, data, repository, tree=None):
    """
    Put a file into a tree, if tree not passed creates a tree.
    Emulate addition or update of files, returns new tree Oid
    """
    from pygit2 import GIT_FILEMODE_BLOB
    blob_oid = repository.create_blob(data)
    TEST_LOGGER.debug("CREATED BLOB : blob.hex : %s" % blob_oid.hex)
    # Put blob into tree
    builder = repository.TreeBuilder(tree) if tree is not None else repository.TreeBuilder()
    builder.insert(name, blob_oid, GIT_FILEMODE_BLOB)
    # Create tree
    tree_oid = builder.write()
    TEST_LOGGER.debug("CREATING TREE : tree.hex : %s" % tree_oid.hex)
    return tree_oid


# Debugging helpers

def debug_branches(repository):
    """
    Outputs all branches of a repository for debugging
    """
    TEST_LOGGER.debug("\nDEBUG BRANCHES for %s" % repository.path)
    for branch_name in repository.listall_branches():
        branch = repository.lookup_branch(branch_name)
        TEST_LOGGER.debug("BRANCH : %s : is head? %s" % (branch.branch_name, branch.is_head()))
    TEST_LOGGER.debug("\n")


def debug_commits(repository, start_commit_oid, end_commit_oid=None):
    """
    Outputs all commits in given range for debugging, with the latest commits first
    """
    from pygit2 import GIT_SORT_TOPOLOGICAL
    TEST_LOGGER.debug("\nDEBUG COMMITS for %s" % repository.path)
    for c in repository.walk(start_commit_oid, GIT_SORT_TOPOLOGICAL):
        TEST_LOGGER.debug("COMMIT : %s - %s by %s @ %s" % (c.hex, c.message, c.author.name, c.commit_time))
        if end_commit_oid and c.hex == end_commit_oid.hex:
            TEST_LOGGER.debug("END COMMIT.")
            break
    TEST_LOGGER.debug("\n")


def debug_tree(repository, tree_oid):
    """
    Debug a tree by outputting all entries
    """
    TEST_LOGGER.debug("\nDEBUG TREE for %s" % repository.path)
    tree = repository.get(tree_oid)
    TEST_LOGGER.debug("LOADED TREE : %d items : %s" % (len(tree), tree.hex))
    for entry in tree:
        TEST_LOGGER.debug("TREE ENTRY : %s - %s" % (entry.name, entry.hex))
    TEST_LOGGER.debug("\n")


class RepositoryTestCase(TestCaseDebugMixin, TestCase):

    def setUp(self):
        super(RepositoryTestCase, self).setUp()
        self.project = Project.objects.get(id=1)
        TEST_LOGGER.debug("LOADED PROJECT : %d : %s" % (self.project.id, self.project.name))
        self.assertEqual(self.project.name, 'joltem')
        self.repository = get_mock_repository("TEST", self.project)
        TEST_LOGGER.debug("CREATED REPO : %s" % self.repository.absolute_path)
        self.assertDirectoryExistence(self.repository.absolute_path, True)
        # Load repo
        self.pygit_repository = PyGitRepository(self.repository.absolute_path)
        TEST_LOGGER.debug("LOADED REPOSITORY : path : %s" % self.pygit_repository.path)
        TEST_LOGGER.debug("LOADED REPOSITORY : workdir : %s" % self.pygit_repository.workdir)
        TEST_LOGGER.debug("LOADED REPOSITORY : is_bare : %s" % self.pygit_repository.is_bare)
        self.assertTrue(self.pygit_repository.is_bare)
        TEST_LOGGER.debug("LOADED REPOSITORY : is_empty : %s" % self.pygit_repository.is_empty)
        self.assertTrue(self.pygit_repository.is_empty)

    def tearDown(self):
        super(RepositoryTestCase, self).tearDown()
        self.repository.delete() # remove the repo
        TEST_LOGGER.debug("DELETED REPO : %s" % self.repository.absolute_path)
        self.assertDirectoryExistence(self.repository.absolute_path, False)

    # Custom assertions

    def assertDirectoryExistence(self, path, expected=True):
        from os.path import isdir
        self.assertEqual(isdir(path), expected)

    # Tests

    def test_pygit2_version(self):
        # Test version
        import pygit2
        expecting = '0.19.0'
        actual = pygit2.__version__
        self.assertEqual(actual, expecting, "Using wrong version of pygit2, expecting %s, installed %s." % (expecting, actual))

    def test_pygit2(self):
        # Create tree
        tree_oid = put_file_to_tree("test_blob.txt", "This is a test blob.", self.pygit_repository)
        tree_oid = put_file_to_tree("test_blob_2.txt", "This is a test blob. With another file.", self.pygit_repository, tree_oid)
        debug_tree(self.pygit_repository, tree_oid)
        # Create commit
        emil = get_mock_signature('emil')
        commit_oid = get_mock_commit(self.pygit_repository, tree_oid, emil, get_branch_reference('master'), "Initial commit.")
        # Run through branches
        debug_branches(self.pygit_repository)

        # Walk through commits
        debug_commits(self.pygit_repository, commit_oid)
