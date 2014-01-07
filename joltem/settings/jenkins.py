""" Settings for Jenkins tests running. """

from .test import *


GATEWAY_PRIVATE_KEY_FILE_PATH = "/var/lib/jenkins/id_rsa"
GATEWAY_PUBLIC_KEY_FILE_PATH = "/var/lib/jenkins/id_rsa.pub"

logging.info("Jenkins settings loaded.")
