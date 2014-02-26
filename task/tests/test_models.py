from django.test import TestCase
from django.core.cache import cache
from joltem.libs import mixer, load_model


class TaskModelTest(TestCase):

    def test_cache_invalidate(self):
        project = mixer.blend('project')
        cache.set('%s:tasks_tabs' % project.pk, True)
        mixer.blend('task', project=project)
        self.assertFalse(cache.get('%s:tasks_tabs' % project.pk))

    def test_add_comment(self):
        task = mixer.blend('task')
        task.add_comment(mixer.blend('user'), 'test')
        _task = load_model(task)
        self.assertEqual(task.time_updated, _task.time_updated)

    def test_add_vote(self):
        task = mixer.blend('task')
        task.put_vote(mixer.blend('user'), True)
        _task = load_model(task)
        self.assertEqual(task.time_updated, _task.time_updated)
