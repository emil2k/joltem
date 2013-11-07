# coding: utf-8
import os

from django.test import TestCase
from django.conf import settings


class PythonRequirementsTest(TestCase):

    def test_requirements_file_exists(self):
        requirements_file_path_expected = os.path.join(
            settings.PROJECT_ROOT, 'requirements.txt'
        )
        self.assertTrue(os.path.exists(requirements_file_path_expected))

    def test_correct_pygit_version_is_in_requirements_file(self):
        requirements_file_path = os.path.join(
            settings.PROJECT_ROOT, 'requirements.txt'
        )
        pygit_version_expected = 'pygit2==0.19.1'

        with open(requirements_file_path) as fh:
            self.assertIn(pygit_version_expected, fh.read())


class PythonServersTest(TestCase):

    def test_twisted_gateway_file_exists(self):
        gateway_file_path_expected = os.path.join(
            settings.PROJECT_ROOT, 'gateway/gateway.tac'
        )
        self.assertTrue(os.path.exists(gateway_file_path_expected))

    def test_django_wsgi_file_exists(self):
        wsgi_file_path_expected = os.path.join(
            settings.PROJECT_ROOT, 'joltem/wsgi.py'
        )
        self.assertTrue(os.path.exists(wsgi_file_path_expected))


class DjangoSettingsTest(TestCase):

    def test_static_url_is_equal_to_nginx_location_block(self):
        static_url_expected = '/static/'
        self.assertEqual(settings.STATIC_URL, static_url_expected)
