""" Mock cache client for support django-redis functionality in tests. """
import fnmatch
from re import compile as re

from django.core.cache.backends.locmem import LocMemCache


class MockCacheClient(LocMemCache):

    """ Supports django-redis functionality with Memory cache-client. """

    def keys(self, pattern):
        """ Add abilite to retrieve a list of keys with wildcard pattern.

        :returns: List keys

        """
        offset = len(self.make_key(''))
        mask = re(fnmatch.translate(self.make_key(pattern)))
        return [k[offset:] for k in self._cache.keys() if mask.match(k)]

    def delete_pattern(self, pattern):
        """ Delete keys by pattern. """
        keys = self.keys(pattern)
        self.delete_many(keys)
