from django.test import TestCase

from joltem.libs import mixer


class GitModelsTest(TestCase):

    def test_save(self):
        key = mixer.blend('git.authentication')
        self.assertTrue(key.fingerprint)
