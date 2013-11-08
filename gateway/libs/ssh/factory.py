""" Load keys and setup factory. """

from twisted.conch.ssh.keys import Key
from twisted.conch.ssh.factory import SSHFactory

from django.conf import settings

SERVER_PRIVATE_KEY = Key.fromFile(settings.GATEWAY_PRIVATE_KEY_FILE_PATH)
SERVER_PUBLIC_KEY = Key.fromFile(settings.GATEWAY_PUBLIC_KEY_FILE_PATH)


class GatewayFactory(SSHFactory):

    """ Factory with preloaded keys. """

    def getPrivateKeys(self):
        """ Load private key.

        :return dict:

        """
        return {'ssh-rsa': SERVER_PRIVATE_KEY}

    def getPublicKeys(self):
        """ Load public key.

        :return dict:

        """
        return {'ssh-rsa': SERVER_PUBLIC_KEY}
