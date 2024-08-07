# Copyright (C) 2007  Matthew Neeley
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# """
# ### BEGIN NODE INFO
# [info]
# name = Data Vault
# version = 3.1.2
# description = Manages interaction with datasets.
#
# [startup]
# cmdline = %PYTHON% %FILE%
# timeout = 20
#
# [shutdown]
# message = 987654321
# timeout = 5
# ### END NODE INFO
# """
from __future__ import absolute_import

import os
import sys
from twisted.internet.defer import inlineCallbacks, returnValue

import labrad.util
import labrad.wrappers

from data_vault_clayton import SessionStore
from data_vault_clayton.server import DataVault
# todo: add support for comments


@inlineCallbacks
def load_settings(cxn, name):
    """
    Load settings from registry with fallback to command line if needed.

    Attempts to load the data vault configuration for this node from the
    registry. If not configured, we instead prompt the user to enter a path
    to use for storing data, and save this config into the registry to be
    used later.
    """
    nodename = labrad.util.getNodeName()

    # get startup values from registry
    path = ['', 'Servers', name, 'Repository']
    reg = cxn.registry
    yield reg.cd(path, True)
    (dirs, keys) = yield reg.dir()

    # look for node-specific directory
    if nodename in keys:
        datadir = yield reg.get(nodename)
    # otherwise, try to get default directory
    elif '__default__' in keys:
        datadir = yield reg.get('__default__')
    # finally, have user assign starting directory
    else:
        default_datadir = os.path.expanduser('~/.labrad/vault')

        # get user input
        print('Could not load repository location from registry.')
        print('Please enter data storage directory or hit enter to use')
        print('the default directory ({}):'.format(default_datadir))
        datadir = os.path.expanduser(input('>>>'))

        # set to default_datadir if empty, and create it if it doesn't exist
        if datadir == '':
            datadir = default_datadir
        if not os.path.exists(datadir):
            os.makedirs(datadir)

        # set as default and for this node
        yield reg.set(nodename, datadir)
        yield reg.set('__default__', datadir)
        print('Data location configured in the registry at {}: {}'.format(path + [nodename], datadir))
        print('To change this, edit the registry keys and restart the server.')

    returnValue(datadir)


def main(argv=sys.argv):
    from twisted.internet import reactor

    @inlineCallbacks
    def start():
        # create connection to labrad
        opts = labrad.util.parseServerOptions(name=DataVault.name)
        cxn = yield labrad.wrappers.connectAsync(
            host=opts['host'], port=int(opts['port']), password=opts['password']
        )
        datadir = yield load_settings(cxn, opts['name'])
        yield cxn.disconnect()

        # create SessionStore
        # if use_virtual_session is set to True, any number of datadirs can be specified in a list
        session_store = SessionStore(datadir, hub=None, use_virtual_session=False)
        server = DataVault(session_store)
        session_store.hub = server

        # Run the server. We do not need to start the reactor, but we will
        # stop it after the data_vault shuts down.
        labrad.util.runServer(server, run_reactor=False, stop_reactor=True)

    _ = start()
    reactor.run()


if __name__ == '__main__':
    main()
