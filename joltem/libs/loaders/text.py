"""
Wrapper for loading text files from "texts" directories in INSTALLED_APPS
packages.

Based on django.template.loaders.app_directories.py with minor alterations.
"""

import sys

import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils._os import safe_join
from django.utils.importlib import import_module
from django.utils import six


TEXTS_DIRECTORY = 'texts'

# At compile time, cache the directories to search.
if not six.PY3:
    fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()
app_text_dirs = []
for app in settings.INSTALLED_APPS:
    try:
        mod = import_module(app)
    except ImportError as e:
        raise ImproperlyConfigured('ImportError %s: %s' % (app, e.args[0]))
    text_dir = os.path.join(os.path.dirname(mod.__file__), TEXTS_DIRECTORY)
    if os.path.isdir(text_dir):
        if not six.PY3:
            text_dir = text_dir.decode(fs_encoding)
        app_text_dirs.append(text_dir)

# It won't change, so convert it to a tuple to save memory.
app_text_dirs = tuple(app_text_dirs)


class TextDoesNotExist(Exception):
    """Thrown when texts file does not exist"""
    pass


class TextLoader():
    def __call__(self, text_name, text_dirs=None):
        return self.load_text_source(text_name, text_dirs)

    def get_text_sources(self, text_name, text_dirs=None):
        """
        Returns the absolute paths to "text_name", when appended to each
        directory in "text_dirs". Any paths that don't lie inside one of the
        text dirs are excluded from the result set, for security reasons.
        """
        if not text_dirs:
            text_dirs = app_text_dirs
        for text_dir in text_dirs:
            try:
                yield safe_join(text_dir, text_name)
            except UnicodeDecodeError:
                # The text dir name was a bytestring that wasn't valid UTF-8.
                raise
            except ValueError:
                # The joined path was located outside of text_dir.
                pass

    def load_text_source(self, text_name, text_dirs=None):
        for filepath in self.get_text_sources(text_name, text_dirs):
            try:
                with open(filepath, 'rb') as fp:
                    return fp.read().decode(settings.FILE_CHARSET), filepath
            except IOError:
                pass
        raise TextDoesNotExist(text_name)
