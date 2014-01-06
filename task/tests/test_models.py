from django.test import TestCase
from django.core.cache import cache
from joltem.libs import mixer


class TaskModelTest(TestCase):

    def test_cache_invalidate(self):
        project = mixer.blend('project')
        cache.set('%s:tasks_tabs' % project.pk, True)
        mixer.blend('task', project=project)
        self.assertFalse(cache.get('%s:tasks_tabs' % project.pk))
