# EXAMPLE
# Local settings file, copy to local.py and alter to fit environment

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Absolute path to main project directory which contains all the apps, with trailing slash
MAIN_DIR = ''

# Absolute path to Joltem logger log, if set outputs to this Joltem logger to file
JOLTEM_LOGGER_FILE_PATH = None
JOLTEM_LOGGER_MAX_BYTES = 500 * 1024 * 1024  # maximum bytes per log file, rotates logs when it reaches this
JOLTEM_LOGGER_BACKUP_COUNT = 5  # how many rotated logs to keep

# Make this unique, and don't share it with anybody, used for hashing passwords
# You can use generator here : http://www.miniwebtool.com/django-secret-key-generator/
SECRET_KEY = ''

# Database connection settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',   # using mysql
        'NAME': '',                             # database name
        'USER': '',                             # database user
        'PASSWORD': '',                         # database password
        'HOST': '',                             # host for database server
        'PORT': '',                             # port for database server
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Gateway settings

GATEWAY_PORT = 22
GATEWAY_PRIVATE_KEY_FILE_PATH = None  # RSA key
GATEWAY_PUBLIC_KEY_FILE_PATH = None

# Fabric deployment settings

# Elastic IP to EC2 instance to deploy to
DEPLOYMENT_ELASTIC_IP = ''
# User to use on EC2 instance for deployment
DEPLOYMENT_USER = ''
# PEM file for accessing EC2 instance to deploy to
DEPLOYMENT_KEY_FILE = ''
# Path on the EC2 instance to deploy to, with trailing slash
DEPLOYMENT_PATH = ''
# Path to python virtualenv activate script on the EC2 instance
DEPLOYMENT_VIRTUALENV_ACTIVATE = ''
# Command to reload UWSGI process on the EC2 instance
DEPLOYMENT_UWSGI_RELOAD_COMMAND = ''

# To speed up tests
import sys
if 'test' in sys.argv:
    SOUTH_TESTS_MIGRATE = False