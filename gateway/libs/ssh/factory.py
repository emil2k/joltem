from twisted.conch.ssh.keys import Key
from twisted.conch.ssh.factory import SSHFactory

from joltem.settings import GATEWAY_PRIVATE_KEY_FILE_PATH, GATEWAY_PUBLIC_KEY_FILE_PATH

# Load server keys

SERVER_PRIVATE_KEY = Key.fromFile(GATEWAY_PRIVATE_KEY_FILE_PATH)
SERVER_PUBLIC_KEY = Key.fromFile(GATEWAY_PUBLIC_KEY_FILE_PATH)


class GatewayFactory(SSHFactory):

    def __init__(self):
        self.privateKeys = {'ssh-rsa': SERVER_PRIVATE_KEY}
        self.publicKeys = {'ssh-rsa': SERVER_PUBLIC_KEY}
