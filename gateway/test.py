
# Start up the server ...

GATEWAY_PORT = 2022

if __name__ == '__main__':
    import sys
    from twisted.python import log
    from twisted.internet import reactor
    from twisted.internet.endpoints import TCP4ServerEndpoint
    from twisted.cred.portal import Portal

    from gateway.libs.ssh.factory import GatewayFactory
    from gateway.libs.ssh.auth import GatewayRealm, DummyEmilChecker

    log.startLogging(sys.stdout)

    factory = GatewayFactory()
    # Setup portal and credential checkers
    portal = Portal(GatewayRealm())
    portal.registerChecker(DummyEmilChecker())
    factory.portal = portal
    # Connect factory on endpoint
    d = TCP4ServerEndpoint(reactor, GATEWAY_PORT).listen(factory)
    d.addCallback(lambda port: log.msg("Listening on port %d." % GATEWAY_PORT))
    d.addErrback(lambda failure: log.err(failure, "Failed to open gateway on port %d." % GATEWAY_PORT))
    # Run reactor :)
    reactor.run()