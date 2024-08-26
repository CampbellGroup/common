from twisted.internet.defer import inlineCallbacks, returnValue
import logging

logger = logging.getLogger(__name__)

"""
The shared connection object allows multiple asynchronous clients to share a single connection to the manager
Version 1.0
"""


class Connection(object):

    def __init__(self, **kwargs):
        self._servers = {}
        self._on_connect = {}
        self._on_disconnect = {}

        if "name" not in kwargs:
            kwargs["name"] = ""
        self.name = kwargs["name"]

    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync

        self.cxn = yield connectAsync(name=self.name)
        yield self.setup_listeners()
        returnValue(self)

    @inlineCallbacks
    def get_server(self, server_name):
        connected = yield self._confirm_connected(server_name)
        if connected:
            returnValue(self._servers[server_name])
        else:
            raise Exception("Not connected")

    @inlineCallbacks
    def add_on_connect(self, server_name, action):
        connected = yield self._confirm_connected(server_name)
        if not connected:
            print("{} Not Available".format(server_name))
            return
        try:
            self._on_connect[server_name].append(action)
        except KeyError:
            self._on_connect[server_name] = [action]

    @inlineCallbacks
    def add_on_disconnect(self, server_name, action):
        connected = yield self._confirm_connected(server_name)
        if not connected:
            print("{} Not Available".format(server_name))
            return
        try:
            self._on_disconnect[server_name].append(action)
        except KeyError:
            self._on_disconnect[server_name] = [action]

    @inlineCallbacks
    def _confirm_connected(self, server_name):
        if server_name not in self._servers:
            try:
                self._servers[server_name] = yield self.cxn[server_name]
            except Exception as e:
                print(e)
                returnValue(False)
        returnValue(True)

    @inlineCallbacks
    def setup_listeners(self):
        yield self.cxn.manager.subscribe_to_named_message(
            "Server Connect", 9898989, True
        )
        yield self.cxn.manager.subscribe_to_named_message(
            "Server Disconnect", 9898989 + 1, True
        )
        yield self.cxn.manager.addListener(
            listener=self.follow_server_connect, source=None, ID=9898989
        )
        yield self.cxn.manager.addListener(
            listener=self.follow_server_disconnect, source=None, ID=9898989 + 1
        )

    @inlineCallbacks
    def follow_server_connect(self, cntx, server_name):
        # print 'server connected'
        server_name = server_name[1]
        if server_name in self._servers.keys():
            print("{} connected".format(server_name))
            yield self.cxn.refresh()
            self._servers[server_name] = yield self.cxn[server_name]
            actions = self._on_connect[server_name]
            for action in actions:
                yield action()
        else:
            logger.info("{} connected".format(server_name))

    @inlineCallbacks
    def follow_server_disconnect(self, cntx, server_name):
        server_name = server_name[1]
        if server_name in self._servers.keys():
            logger.info("{} Disconnected".format(server_name))
            self._servers[server_name] = None
            actions = self._on_disconnect[server_name]
            for action in actions:
                yield action()

    @inlineCallbacks
    def context(self):
        context = yield self.cxn.context()
        returnValue(context)


if __name__ == "__main__":
    from twisted.internet import reactor

    app = Connection()
    reactor.callWhenRunning(app.connect)
    reactor.run()
