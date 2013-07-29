from fabric.api import *
from joltem.settings.local import DEPLOYMENT_ELASTIC_IP, DEPLOYMENT_KEY_FILE, DEPLOYMENT_USER, DEPLOYMENT_PATH, DEPLOYMENT_VIRTUALENV_ACTIVATE, DEPLOYMENT_UWSGI_RELOAD_COMMAND


def headline(text):
    if text:
        from fabric.colors import green
        print(green(text, bold=True))


def info(text):
    if text:
        from fabric.colors import blue
        print(blue(text, bold=True))

def deploy(branch='master', remote='origin'):
    """
    Deploy to the EC2 instance
    Examples :
    # To deploy master branch from remote origin run ...
    fab deploy
    # To deploy develop branch from remote test run ...
    fab deploy:develop,test
    """
    headline('Start deployment : %s from %s' % (branch, remote))
    # Elastic IP to instance
    env.host_string = DEPLOYMENT_ELASTIC_IP
    # User on the system
    env.user = DEPLOYMENT_USER
    # *.pem key file for accessing instance, assumed to be in same directory as this file
    env.key_filename = DEPLOYMENT_KEY_FILE
    # Path to the working directory
    with cd(DEPLOYMENT_PATH):
        info('Switched to deployment directory.')
        run('pwd')
        # Fetch branches from the remote
        info('Fetch remote branches from %s.' % remote)
        sudo('git remote show %s' % remote)
        sudo('git fetch -v %s' % remote)
        # Checkout remote branch, throws away local changes, if already exists reset to this
        info('Checkout local remote branch %s/%s.' % (remote, branch))
        sudo('git checkout -fB {0} {1}/{0}'.format(branch, remote))
        with(prefix('source %s' % DEPLOYMENT_VIRTUALENV_ACTIVATE)):
            # Install requirements
            info('Installing requirements.')
            run('pip install -r %sjoltem/requirements.txt' % DEPLOYMENT_PATH)
            # Collect static files
            info('Collecting static files.')
            sudo('python manage.py collectstatic --noinput')  # make sure static folder has write permissions
            # Sync the database
            info('Synchronizing database.')
            run('python manage.py syncdb --noinput')  # create superuser later if it is the first time
            # Migrate the database
            info('Migrating database.')
            run('python manage.py migrate')
            # Load initial data into database
            info('Load initial data.')
            run('python manage.py loaddata initial_data.yaml')
        # Restart UWSGI process
        info('Restarting UWSGI process.')
        run(DEPLOYMENT_UWSGI_RELOAD_COMMAND)




