""" Implement SSH authentication. """
import os
import sys

from django.conf import settings
from gitserverglue import ssh
from twisted.conch.ssh.keys import Key
from twisted.internet import reactor
from twisted.python import log

from git.models import Authentication, BadKeyError
from joltem.models import User


class JoltemAuth(object):

    """ Check Joltem users. """

    def can_read(self, username, path_info):
        """ Check for user can read from path.

        :return bool:

        """
        return self._check_access(username, path_info, "r")

    def can_write(self, username, path_info):
        """ Check for user can write from path.

        :return bool:

        """
        return self._check_access(username, path_info, "w")

    @staticmethod
    def _check_access(username, path_info, level):

        if username is None:
            username = "anonymous"

        log.msg('Try to auth %s' % username)

        if path_info['repository_fs_path'] is None:
            return False

        log.msg('Path info', path_info)

        try:
            User.objects.get(username=username)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return False

        log.msg('%s authenticated' % username)

        return True

    @staticmethod
    def check_publickey(username, keyblob):
        """ Check user's keys.

        :return bool:

        """
        try:
            user = User.objects.get(username=username)
            key = Authentication.load_key(keyblob)
            provided_fp = key.fingerprint()
            return user.authentication_set.filter(
                fingerprint=provided_fp).exists()

        except (User.DoesNotExist, User.MultipleObjectsReturned, BadKeyError):
            return False

    @staticmethod
    def check_password(username, password):
        """ Check password.

        :return bool:

        """
        try:
            user = User.objects.get(username=username)
            return user.check_password(password)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return False


class JoltemGitConfiguration(object):

    """ Configure Joltem repository. """

    git_binary = 'git'
    git_shell_binary = 'git-shell'

    @staticmethod
    def path_lookup(url, protocol_hint=None):
        """ Lookup path.

        :return dict:

        """
        res = {
            'repository_base_fs_path': settings.GATEWAY_REPOSITORIES_DIR,
            'repository_base_url_path': '/',
            'repository_fs_path': None
        }

        pathparts = url.strip('/').split('/')
        log.msg(pathparts)

        if len(pathparts) > 0 and pathparts[0].endswith('.git'):
            p = os.path.join(settings.GATEWAY_REPOSITORIES_DIR, pathparts[0])
            if os.path.exists(p):
                res['repository_fs_path'] = p
                res['repository_clone_urls'] = {
                    'http': 'http://localhost:8080/' + pathparts[0],
                    'git': 'git://localhost/' + pathparts[0],
                    'ssh': 'ssh://localhost:5522/' + pathparts[0]
                }

        log.msg(res)

        return res


ssh_factory = ssh.create_factory(
    public_keys={'ssh-rsa': Key.fromFile(
        settings.GATEWAY_PRIVATE_KEY_FILE_PATH)},
    private_keys={'ssh-rsa': Key.fromFile(
        settings.GATEWAY_PUBLIC_KEY_FILE_PATH)},
    authnz=JoltemAuth(),
    git_configuration=JoltemGitConfiguration()
)

if __name__ == '__main__':
    log.startLogging(sys.stdout)

    reactor.listenTCP(settings.GATEWAY_PORT, ssh_factory)
    reactor.run()

else:
    from twisted.application import service, internet
    application = service.Application("Gateway")

    server = internet.TCPServer(settings.GATEWAY_PORT, ssh_factory)
    server.setServiceParent(application)
