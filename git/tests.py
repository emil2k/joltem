from django.test import TestCase

from git.models import Repository
from project.models import Project

from joltem.tests import TEST_LOGGER, TestCaseDebugMixin
from joltem.tests.mocking import get_mock_project, get_mock_repository


class RepositoryTestCase(TestCaseDebugMixin, TestCase):

    def setUp(self):
        super(RepositoryTestCase, self).setUp()
        self.project = Project.objects.get(id=1)
        TEST_LOGGER.debug("LOADED PROJECT : %d : %s" % (self.project.id, self.project.name))
        self.repository = get_mock_repository("TEST", self.project)
        TEST_LOGGER.debug("CREATED REPO : %s" % self.repository.absolute_path)
        self.assertDirectoryExistence(self.repository.absolute_path, True)

    def tearDown(self):
        self.repository.delete() # remove the repo
        TEST_LOGGER.debug("DELETED REPOS : ")
        self.assertDirectoryExistence(self.repository.absolute_path, False)
        super(RepositoryTestCase, self).tearDown()

    # Custom assertions

    def assertDirectoryExistence(self, path, expected=True):
        from os.path import isdir
        self.assertEqual(isdir(path), expected)

    # Tests

    def test_simple(self):
        self.assertEqual(self.project.name, 'joltem')

    def test_pygit2(self):
        # Test version
        import pygit2
        expecting = '0.19.0'
        actual = pygit2.__version__
        self.assertEqual(actual, expecting, "Using wrong version of pygit2, expecting %s, installed %s." % (expecting, actual))