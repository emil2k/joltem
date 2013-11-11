""" Loader related tests. """

from django.test import TestCase

from joltem.libs.loaders.text import TextLoader, app_text_dirs


class TextsLoaderTestCase(TestCase):

    def setUp(self):
        self.text_name = "joltem/introduction.md"
        self.loader = TextLoader()

    # Custom assertions

    def assertFileExists(self, filepath):
        """
        Checks that a file exists
        """
        try:
            with open(filepath):
                pass
        except IOError:
            self.failureException("File does not exist at %s." % filepath)

    # Tests

    def test_directory_cache(self):
        self.assertTrue(len(app_text_dirs) > 0)

    def test_text_sources(self):
        for source in self.loader.get_text_sources(self.text_name):
            self.assertFileExists(source)

    def test_loading_text(self):
        text, filepath = self.loader(self.text_name)
        self.assertIn("work", text.lower())


