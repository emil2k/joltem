from twisted.conch.ssh.keys import Key
from twisted.conch.ssh.factory import SSHFactory

# Load server keys

SERVER_PRIVATE_KEY = Key.fromFile("id_rsa")
SERVER_PUBLIC_KEY = Key.fromFile("id_rsa.pub")


class GatewayFactory(SSHFactory):

    def __init__(self):
        self.privateKeys = {'ssh-rsa': SERVER_PRIVATE_KEY}
        self.publicKeys = {'ssh-rsa': SERVER_PUBLIC_KEY}
