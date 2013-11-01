""" Setup wsgi application. """

import os

ROOT = os.path.abspath(os.path.dirname(__file__))

os.environ['PYPI_PROXY_BASE_FOLDER_PATH'] = os.path.join(ROOT, 'packages')
os.environ['PYPI_PROXY_LOGGING_PATH'] = os.path.join(ROOT, 'pypi.log')

from flask_pypi_proxy.views import app
assert app
