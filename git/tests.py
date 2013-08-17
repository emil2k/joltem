from django.test import TestCase
from unittest import TestCase as UnitTestCase

from git.models import Repository
from project.models import Project

from joltem.tests import TEST_LOGGER, TestCaseDebugMixin
from joltem.tests.mocking import *

from pygit2 import Repository as PyGitRepository, Signature


# Mocking helpers


def get_mock_repository(name, project, is_hidden=False, description=None):
    r = Repository(
        name=name,
        project=project,
        is_hidden=is_hidden,
        description=description
    )
    r.save()
    return r


def get_mock_signature(name, email=None):
    """
    Get a mock signature object from pygit2
    """
    email = '%s@gmail.com' % name if email is None else email
    return Signature(name, email)


def get_mock_commit(repository, tree_oid, signature, reference, message, parents):
    """
    Make a mock commit to the given repository, returns commit Oid
    """
    commit_oid = repository.create_commit(
        reference,              # reference to update
        signature,              # author
        signature,              # committer
        message,                # message
        tree_oid,               # commit tree, representing file structure
        parents                 # commit parents
    )
    TEST_LOGGER.debug("CREATED COMMIT : %s - %s" % (commit_oid.hex, commit_oid))
    return commit_oid


def put_mock_file(name, data, repository, tree=None):
    """
    Put a mock file into a tree, if tree not passed creates a tree.
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
    debug_tree(repository, tree_oid)
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
        TEST_LOGGER.debug("COMMIT : %s - %s by %s @ %s - parents %d" % (c.hex, c.message, c.author.name, c.commit_time, len(c.parents)))
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


# Test cases

class PyGit2TestCase(TestCaseDebugMixin, UnitTestCase):

    def test_pygit2_version(self):
        """
        Test pygit2 version matches expectations
        """
        import pygit2
        expecting = '0.19.0'
        actual = pygit2.__version__
        self.assertEqual(actual, expecting, "Using wrong version of pygit2, expecting %s, installed %s." % (expecting, actual))


class RepositoryTestCase(TestCaseDebugMixin, TestCase):

    """
    Base test case class that loads a project, creates a repository,
    and loads a pygit2 repository object for the repository.
    Deletes the repository in teardown.
    """

    def setUp(self):
        super(RepositoryTestCase, self).setUp()
        self.project = Project.objects.get(id=1)
        TEST_LOGGER.debug("LOADED PROJECT : %d : %s" % (self.project.id, self.project.name))
        self.assertEqual(self.project.name, 'joltem')
        self.repository = get_mock_repository("TEST", self.project)
        TEST_LOGGER.debug("CREATED REPO : %s" % self.repository.absolute_path)
        self.assertDirectoryExistence(self.repository.absolute_path, True)
        # Load repo
        self.pygit_repository = self.repository.load_pygit_object()
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


class SolutionTestCase(RepositoryTestCase):
    """
    Tests regarding solution branches
    """

    def setUp(self):
        super(SolutionTestCase, self).setUp()
        self.emil = get_mock_user("emil", first_name="Emil")
        self.emil_signature = get_mock_signature(self.emil.first_name, self.emil.email)
        self.solution = get_mock_solution(self.project, self.emil)  # a suggested solution

    def test_reference(self):
        self.assertEqual(self.solution.get_reference(), 'refs/heads/s/%d' % self.solution.id)

    def test_parent_reference_through_task(self):
        self.assertEqual(self.solution.get_parent_reference(), 'refs/heads/master') # default solution is a suggested solution
        # Add it to a task to a root task
        task = get_mock_task(self.project, get_mock_user('jill'))
        self.solution.task = task
        self.solution.save()
        self.assertEqual(self.solution.get_parent_reference(), 'refs/heads/master') # still should default to master because branching from a root task
        # Add a parent solution for the parent task
        parent_solution = get_mock_solution(self.project, get_mock_user('zack'))
        task.parent = parent_solution
        task.save()
        self.assertEqual(self.solution.get_parent_reference(), 'refs/heads/s/%d' % parent_solution.id) # now it should be the parent solution

    def test_parent_reference_through_solution(self):
        self.assertEqual(self.solution.get_parent_reference(), 'refs/heads/master') # default solution is a suggested solution
        # Add a parent solution
        parent_solution = get_mock_solution(self.project, get_mock_user('zack'))
        self.solution.solution = parent_solution
        self.solution.save()
        self.assertEqual(self.solution.get_parent_reference(), 'refs/heads/s/%d' % parent_solution.id) # now it should be the parent solution

    # TODO make some solution commit_set property that returns an iterable of commits for a solution then test it here for order
    # TODO then make function that provides diff of solution and then run tests that check on the diff provided and the patches that it generates

    def test_solution_commits(self):
        from git.utils import get_branch_reference
        # Make initial commit to master
        tree_oid = put_mock_file("test_blob.txt", "This is a test file.", self.pygit_repository)
        commit_oid = get_mock_commit(
            self.pygit_repository,
            tree_oid,
            self.emil_signature,
            get_branch_reference('master'),
            "Initial commit to master.",
            []  # no parents initial commit
        )
        debug_branches(self.pygit_repository)

        solution_commits = []
        # Now make a commit to the solution branch
        tree_oid = put_mock_file("test_blob_2.txt", "This is a test blob.\nWith another file.", self.pygit_repository, tree_oid)
        commit_oid = get_mock_commit(
            self.pygit_repository,
            tree_oid,
            self.emil_signature,
            get_branch_reference('s/%d' % self.solution.id),
            "First commit to solution branch.",
            [commit_oid]
        )
        debug_branches(self.pygit_repository)
        solution_commits.append(commit_oid)

        # Now modify the file again
        tree_oid = put_mock_file(
            "test_blob_2.txt",
            "This is a test blob.\nWith another file.\nIt's me ... again.",
            self.pygit_repository,
            tree_oid
        )
        commit_oid = get_mock_commit(
            self.pygit_repository,
            tree_oid,
            self.emil_signature,
            get_branch_reference('s/%d' % self.solution.id),
            "Modified file on solution branch.",
            [commit_oid]
        )
        debug_branches(self.pygit_repository)
        solution_commits.append(commit_oid)

        # Walk through commits
        debug_commits(self.pygit_repository, commit_oid)

        # Now compare to expectations
        solution_commits.reverse()
        commit_set = self.solution.get_commit_set(self.pygit_repository)

        TEST_LOGGER.debug("SOLUTION COMMITS : %s" % [commit.hex for commit in solution_commits])
        TEST_LOGGER.debug("COMMIT SET: %s" % [commit.hex for commit in commit_set])

        self.assertListEqual(solution_commits, commit_set)

    # TODO test commit_sets of solutions that are branched out from another solution branch
    # TODO test commit_sets of solution that are branched from closed or completed solutions
    # TODO check a scenario where multiple solution branches are being committed to at same time in an alternating sequence and check that both get right commits in their commit_set
    # TODO test merging from one solution branch to another to check if commit_set remains valid

