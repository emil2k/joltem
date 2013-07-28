from fabric.api import *
from fabric.colors import green, blue, red
from joltem.settings.local import DEPLOYMENT_ELASTIC_IP, DEPLOYMENT_KEY_FILE, DEPLOYMENT_USER, DEPLOYMENT_PATH


def deploy():
    """
    Deploy to the EC2 instance
    """
    print(blue('Start Deployment'))
    # Elastic IP to instance
    env.host_string = DEPLOYMENT_ELASTIC_IP
    # User on the system
    env.user = DEPLOYMENT_USER
    # *.pem key file for accessing instance, assumed to be in same directory as this file
    env.key_filename = DEPLOYMENT_KEY_FILE
    # Path to the working directory
    with cd(DEPLOYMENT_PATH):
        run('git status')
