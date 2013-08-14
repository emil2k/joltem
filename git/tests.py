from django.test import TestCase

from git.models import Repository
from project.models import Project

from joltem.tests import TEST_LOGGER, TestCaseDebugMixin
from joltem.tests.mocking import get_mock_project, get_mock_repository


# TODO create a mock commit
# TODO create a mock branch

class RepositoryTestCase(TestCaseDebugMixin, TestCase):

    def setUp(self):
        super(RepositoryTestCase, self).setUp()
        self.project = Project.objects.get(id=1)
        TEST_LOGGER.debug("LOADED PROJECT : %d : %s" % (self.project.id, self.project.name))
        self.assertEqual(self.project.name, 'joltem')
        self.repository = get_mock_repository("TEST", self.project)
        TEST_LOGGER.debug("CREATED REPO : %s" % self.repository.absolute_path)
        self.assertDirectoryExistence(self.repository.absolute_path, True)

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
        from pygit2 import Repository as GitRepository, GIT_FILEMODE_BLOB, Signature, GIT_SORT_TOPOLOGICAL

        # Load repo
        r = GitRepository(self.repository.absolute_path)
        TEST_LOGGER.debug("LOADED REPOSITORY : path : %s" % r.path)
        TEST_LOGGER.debug("LOADED REPOSITORY : workdir : %s" % r.workdir)
        TEST_LOGGER.debug("LOADED REPOSITORY : is_bare : %s" % r.is_bare)
        self.assertTrue(r.is_bare)
        TEST_LOGGER.debug("LOADED REPOSITORY : is_empty : %s" % r.is_empty)
        self.assertTrue(r.is_bare)

        # Create a blob
        from pygit2 import hash
        data = "test blob"
        TEST_LOGGER.debug("CREATING BLOB : hash : %s" % hash(data).hex)
        blob_oid = r.create_blob(data)
        TEST_LOGGER.debug("CREATING BLOB : blob.hex : %s" % blob_oid.hex)

        # Put blob into tree
        builder = r.TreeBuilder()
        builder.insert("test_blob", blob_oid, GIT_FILEMODE_BLOB)

        # Create tree
        tree_oid = builder.write()
        TEST_LOGGER.debug("CREATING TREE : tree.hex : %s" % tree_oid.hex)
        tree = r.get(tree_oid)
        TEST_LOGGER.debug("LOADED TREE : len(tree) : %d" % len(tree))
        for entry in tree:
            TEST_LOGGER.debug("LOADED TREE ENTRY : %s - %s - %s" % (entry.name, entry.hex, entry.filemode))

        # Create commit
        sig = Signature("Emil", "emil2k@gmail.com")
        commit = r.create_commit(
            'refs/heads/master',    # reference to update
            sig,                    # author
            sig,                    # committer
            "Initial commit.",      # message
            tree.oid,               # commit tree, representing file structure
            []                      # todo commit parents?
        )
        TEST_LOGGER.debug("CREATED COMMIT : %s - %s" % (commit.hex, commit))

        # Run through branches
        for branch_name in r.listall_branches():
            branch = r.lookup_branch(branch_name)
            TEST_LOGGER.debug("BRANCH : %s : is head? %s" % (branch.branch_name, branch.is_head()))

        # Walk through commits
        for c in r.walk(commit, GIT_SORT_TOPOLOGICAL):
            TEST_LOGGER.debug("WALK : %s - %s by %s @ %s" % (c.hex, c.message, c.author.name, c.commit_time))