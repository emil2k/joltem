""" Tests for git app. """

import uuid
import pygit2
from datetime import datetime
from os.path import isdir
from mixer.backend.django import mixer
from unittest import TestCase as UnitTestCase
from django.utils import timezone
from django.test import TestCase

from git.utils import get_checkout_oid, get_branch_reference
from git.models import Repository
from project.models import Project
from joltem.libs.mock.models import (get_mock_user, get_mock_solution,
                                  get_mock_task)


def get_mock_repository(name, project, is_hidden=False, description=None):
    """ Setup a mock project and repository.

    Returns a Repository object.

    """
    r = Repository(
        name=name,
        project=project,
        is_hidden=is_hidden,
        description=description
    )
    r.save()
    return r


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


# Test cases

class PyGit2TestCase(UnitTestCase):

    """ Tests related to pygit2 module. """

    def test_pygit2_version(self):
        """ Test pygit2 version matches expectations. """
        expecting = '0.19.1'
        actual = pygit2.__version__
        self.assertEqual(
            actual, expecting,
            "Using wrong version of pygit2, expecting %s, installed %s." %
            (expecting, actual))


class RepositoryTestCase(TestCase):

    """ Test containing a repository.

    Base test case class that loads a project, creates a repository,
    and loads a pygit2 repository object for the repository.
    Deletes the repository in teardown.

    """

    def setUp(self):
        """ Setup project and repository. """
        self.project = mixer.blend(Project, name='joltem')
        self.assertEqual(self.project.name, 'joltem')
        self.repository = get_mock_repository("TEST", self.project)
        self.assertDirectoryExistence(self.repository.absolute_path, True)

        # Load repo
        self.pygit_repository = self.repository.load_pygit_object()
        self.assertTrue(self.pygit_repository.is_bare)

    def tearDown(self):
        """ Teardown repository. """
        super(RepositoryTestCase, self).tearDown()
        rpath = self.repository.absolute_path
        self.repository.delete()  # remove the repo
        self.assertDirectoryExistence(rpath, False)

    # Custom assertions

    def assertDirectoryExistence(self, path, expected=True):
        """ Assert directory exists or not. """
        self.assertEqual(isdir(path), expected)


class SolutionTestCase(RepositoryTestCase):

    """ Tests regarding solution branches. """

    def setUp(self):
        """ Setup a user, signature, and solution. """
        super(SolutionTestCase, self).setUp()
        self.emil = get_mock_user("emil", first_name="Emil")
        self.emil_signature = get_mock_signature(self.emil.first_name,
                                                 self.emil.email)
        self.solution = get_mock_solution(self.project, self.emil)  # a suggested solution

    # Custom assertions

    def assertOidEqual(self, actual, expected):
        """ Assert that object ids match expectation.

        Alters debugging messages to include Oid.hex.

        """
        self.assertEqual(
            actual, expected, "Oids don't match : %s != %s" %
                              (actual.hex, expected.hex))

    def assertCommitRangeEqual(self, solution_oid, checkout_oid):
        """ Assert that commit range of solution matches expectations. """
        range_solution_oid, range_checkout_oid = \
            self.solution.get_pygit_solution_range(self.pygit_repository)
        self.assertOidEqual(range_checkout_oid, checkout_oid)
        self.assertOidEqual(range_solution_oid, solution_oid)
        self.assertOidEqual(
            self.solution.get_pygit_checkout(self.pygit_repository),
            checkout_oid)

    def assertCommitOidSetEqual(self, expected_commit_oid_set, solution=None):
        """ Assert two commit set matches expectations.

        Prints out some debugging info.

        """
        if solution is None:
            solution = self.solution
        commit_oid_set = solution.get_commit_oid_set(self.pygit_repository)
        self.assertListEqual(expected_commit_oid_set, commit_oid_set)

# todo Diff tests


class ReferenceTestCase(SolutionTestCase):

    """ Tests regarding references. """

    def test_reference(self):
        """ Test solution reference name. """
        self.assertEqual(self.solution.get_reference(),
                         'refs/heads/s/%d' % self.solution.id)

    def test_parent_reference_through_task(self):
        """ Test solution's parent reference name through task. """
        self.assertEqual(self.solution.get_parent_reference(),
                         'refs/heads/master')  # default solution is a suggested solution
        # Add it to a task to a root task
        task = get_mock_task(self.project, get_mock_user('jill'),
                             is_reviewed=True, is_accepted=True)
        self.solution.task = task
        self.solution.save()
        self.assertEqual(self.solution.get_parent_reference(),
                         'refs/heads/master')  # still should default to master because branching from a root task
        # Add a parent solution for the parent task
        parent_solution = get_mock_solution(self.project, get_mock_user('zack'))
        task.parent = parent_solution
        task.save()
        self.assertEqual(self.solution.get_parent_reference(),
                         'refs/heads/s/%d' % parent_solution.id)  # now it should be the parent solution

    def test_parent_reference_through_solution(self):
        """ Test solution's parent reference name through solution. """
        self.assertEqual(self.solution.get_parent_reference(),
                         'refs/heads/master')  # default solution is a suggested solution
        # Add a parent solution
        parent_solution = get_mock_solution(self.project, get_mock_user('zack'))
        self.solution.solution = parent_solution
        self.solution.save()
        self.assertEqual(self.solution.get_parent_reference(),
                         'refs/heads/s/%d' % parent_solution.id)  # now it should be the parent solution


class CommitSetTestCase(SolutionTestCase):

    """ Tests regarding commit sets. """

    def test_child_solution_commit_set_parent_closed(self):
        """ Test commit set of a solution.

        A solution that is branched out of another solution branch,
        which is mark closed.

        """
        commit_oid = make_mock_commit(self.pygit_repository,
                                      self.emil_signature, "master", [])

        # Now checkout the parent solution branch
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [commit_oid])

        # Create suggested solution for this solution branch and make a few commits to it
        child_solution = get_mock_solution(self.project, self.emil,
                                           solution=self.solution)
        child_solution_commits = [c for c in mock_commits(
            3, self.pygit_repository, self.emil_signature,
            child_solution.get_branch_name(), [commit_oid])]
        commit_oid = child_solution_commits[-1]

        # Test commit set
        child_solution_commits.reverse()
        self.assertCommitOidSetEqual(child_solution_commits,
                                     solution=child_solution)

        # Now mark the parent solution and closed and check again
        # todo this should be some function on the model
        self.solution.is_closed = True
        self.solution.time_closed = timezone.now()
        self.assertCommitOidSetEqual(child_solution_commits,
                                     solution=child_solution)

        # Now reopen the solution and mark it complete and check
        self.solution.is_closed = False
        self.solution.is_completed = True
        self.solution.time_closed = None
        self.solution.time_completed = timezone.now()
        self.assertCommitOidSetEqual(child_solution_commits,
                                     solution=child_solution)

    def test_child_solution_commit_set(self):
        """ Test commit set of solution.

        Solution that is branched out from another solution branch.

        """
        commit_oid = make_mock_commit(self.pygit_repository,
                                      self.emil_signature, "master", [])
        master_oid = commit_oid

        # Now checkout the parent solution branch
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [commit_oid])
        parent_solution_oid = commit_oid

        # Create suggested solution for this branch and make a few commits to it
        child_solution = get_mock_solution(self.project, self.emil,
                                           solution=self.solution)
        child_solution_commits = [c for c in mock_commits(
            3, self.pygit_repository, self.emil_signature,
            child_solution.get_branch_name(), [commit_oid])]
        commit_oid = child_solution_commits[-1]

        # Test commit set
        child_solution_commits.reverse()
        self.assertCommitOidSetEqual(child_solution_commits,
                                     solution=child_solution)

        # Now merge the commit into parent and check
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [parent_solution_oid, commit_oid])
        self.assertCommitOidSetEqual(child_solution_commits,
                                     solution=child_solution)

        # And merge into master and check
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master",
            [master_oid, commit_oid])
        self.assertCommitOidSetEqual(child_solution_commits,
                                     solution=child_solution)

    def test_solution_commits(self):
        """ Test solution commit set. """
        # Make initial commit to master
        commit_oid = make_mock_commit(self.pygit_repository,
                                      self.emil_signature, "master", [])
        parent_oid = commit_oid  # to test get_parent_pygit_branch
        checkout_oid = commit_oid

        solution_commits = []
        # Now make a commit to the solution branch
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [commit_oid])
        solution_commits.append(commit_oid)

        # Now modify the file again
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [commit_oid])
        solution_commits.append(commit_oid)
        solution_oid = commit_oid  # to test get_pygit_branch

        # Test get pygit branch methods
        self.assertEqual(self.solution.get_pygit_branch(
            self.pygit_repository).resolve().target, solution_oid)
        self.assertEqual(self.solution.get_parent_pygit_branch(
            self.pygit_repository).resolve().target, parent_oid)

        # Test commit range
        self.assertCommitRangeEqual(solution_oid, checkout_oid)

        # Now compare to expectations
        solution_commits.reverse()
        self.assertCommitOidSetEqual(solution_commits)

    def test_merged_solution_commits(self):
        """ Test commit set of merged solution. """

        # Commits to master
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master", [])  # initial commit
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master", [commit_oid])  # another commit
        checkout_oid = commit_oid
        master_oid = commit_oid

        solution_commits = []
        # Commits to solution branch
        solution_commits = [c for c in mock_commits(
            5, self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [commit_oid])]
        commit_oid = solution_commits[-1]
        solution_oid = commit_oid

        # Merge solution branch into master
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            "master", [master_oid, solution_oid])
        master_oid = commit_oid

        # Test range and commit set
        solution_commits.reverse()
        self.assertCommitRangeEqual(solution_oid, checkout_oid)
        self.assertCommitOidSetEqual(solution_commits)

        # Add on commit
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master", [commit_oid])
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master", [commit_oid])

        # Test range again
        self.assertCommitRangeEqual(solution_oid, checkout_oid)
        self.assertCommitOidSetEqual(solution_commits)


class CheckoutTestCase(SolutionTestCase):

    """ Tests regarding finding initial checkout oid. """

    def test_get_initial_checkout_oid(self):
        """ Test for utility function get_initial_checkout_oid(). """
        # Commits to master
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master", [])  # initial commit
        parent_oid = commit_oid
        checkout_oid = commit_oid

        # Commits to solution branch
        commit_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [commit_oid])
        topic_oid = commit_oid

        self.assertEqual(get_checkout_oid(
            self.pygit_repository, topic_oid, parent_oid), checkout_oid)

    def test_get_initial_checkout_oid_concurrent(self):
        """ Test utility function get_initial_checkout_oid(). """
        # Commits to master
        parent_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master", [])  # initial commit
        parent_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master", [parent_oid])
        parent_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master", [parent_oid])

        checkout_oid = parent_oid

        # Concurrent commits to both branches
        topic_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [parent_oid])

        parent_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master", [parent_oid])
        topic_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [topic_oid])
        parent_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master", [parent_oid])
        topic_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [topic_oid])
        parent_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            "master", [parent_oid])
        topic_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [topic_oid])

        self.assertOidEqual(get_checkout_oid(
            self.pygit_repository, topic_oid, parent_oid), checkout_oid)

    def test_get_initial_checkout_oid_merge_to_topic(self):
        """ Test for utility function get_initial_checkout_oid().

        Performs a merge from a parent branch to topic branch, then
        tests initial checkout oid.

        """
        # Commits to master
        parent_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master", [])  # initial commit

        # Checkout topic
        checkout_oid = parent_oid
        topic_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [parent_oid])

        # Make some commits on master
        parent_oid = [c for c in mock_commits(
            3, self.pygit_repository, self.emil_signature,
            "master", [parent_oid])][-1]

        # Merge master commits to topic branch
        topic_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [topic_oid, parent_oid])
        topic_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [topic_oid])

        self.assertOidEqual(get_checkout_oid(
            self.pygit_repository, topic_oid, parent_oid), checkout_oid)

    def test_get_initial_checkout_oid_merge(self):
        """ Test for utility function get_initial_checkout_oid().

        Where a topic branch is merged into parent branch.

        """
        # Commits to master
        parent_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature, "master", [])  # initial commit

        # Checkout topic
        checkout_oid = parent_oid

        topic_oid = [c for c in mock_commits(
            4, self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [parent_oid])][-1]

        # Merge topic into parent branch
        parent_oid = make_mock_commit(
            self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [parent_oid, topic_oid])

        self.assertOidEqual(get_checkout_oid(
            self.pygit_repository, topic_oid, parent_oid), checkout_oid)

        # Now make some more commits on parent branch and check
        parent_oid = [c for c in mock_commits(
            3, self.pygit_repository, self.emil_signature,
            self.solution.get_branch_name(), [parent_oid])][-1]

        self.assertOidEqual(get_checkout_oid(
            self.pygit_repository, topic_oid, parent_oid), checkout_oid)
