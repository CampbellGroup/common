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
"""
### BEGIN NODE INFO
[info]
name = Data Vault
version = 2.6
description =
instancename = Data Vault

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, Signal, setting

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
import numpy

from configparser import ConfigParser as SafeConfigParser
import os
import sys
from datetime import datetime

from errors import *
from dataset import Dataset, Image
from globals import Globals
import helpers

# TODO: tagging
# - search globally (or in some subtree of sessions) for matching tags
#     - this is the least common case, and will be an expensive operation
#     - don't worry too much about optimizing this
#     - since we won't bother optimizing the global search case, we can store
#       tag information in the session


# filename translation

class Session(object):
    """Stores information about a directory on disk.

    One session object is created for each data directory accessed.
    The session object manages reading from and writing to the config
    file, and manages the datasets in this directory.
    """
    # keep a dictionary of all created session objects
    _sessions = {}

    @classmethod
    def get_all(cls):
        return cls._sessions.values()

    @staticmethod
    def exists(path):
        """Check whether a session exists on disk for a given path.

        This does not tell us whether a session object has been
        created for that path.
        """
        return os.path.exists(helpers.file_dir(path))

    def __new__(cls, path, parent):
        """Get a Session object.

        If a session already exists for the given path, return it.
        Otherwise, create a new session instance.
        """
        path = tuple(path)
        if path in cls._sessions:
            return cls._sessions[path]
        inst = super(Session, cls).__new__(cls)
        inst._init(path, parent)
        cls._sessions[path] = inst
        return inst

    def _init(self, path, parent):
        """Initialization that happens once when session object is created."""
        self.path = path
        self.parent = parent
        self.dir = helpers.file_dir(path)
        self.infofile = os.path.join(self.dir, 'session.ini')
        self.datasets = {}

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

            # notify listeners about this new directory
            parent_session = Session(path[:-1], parent)
            parent.onNewDir(path[-1], parent_session.listeners)

        if os.path.exists(self.infofile):
            self.load()
        else:
            self.counter = 1
            self.created = self.modified = datetime.now()
            self.session_tags = {}
            self.dataset_tags = {}

        self.access()  # update current access time and save
        self.listeners = set()

    def load(self):
        """Load info from the session.ini file."""
        s = SafeConfigParser()
        s.read(self.infofile)

        sec = 'File System'
        self.counter = s.getint(sec, 'Counter')

        sec = 'Information'
        self.created = helpers.time_from_str(s.get(sec, 'Created'))
        self.accessed = helpers.time_from_str(s.get(sec, 'Accessed'))
        self.modified = helpers.time_from_str(s.get(sec, 'Modified'))

        # get tags if they're there
        if s.has_section('Tags'):
            self.session_tags = eval(s.get('Tags', 'sessions', raw=True))
            self.dataset_tags = eval(s.get('Tags', 'datasets', raw=True))
        else:
            self.session_tags = {}
            self.dataset_tags = {}

    def save(self):
        """Save info to the session.ini file."""
        s = SafeConfigParser()

        sec = 'File System'
        s.add_section(sec)
        s.set(sec, 'Counter', repr(self.counter))

        sec = 'Information'
        s.add_section(sec)
        s.set(sec, 'Created', helpers.time_to_str(self.created))
        s.set(sec, 'Accessed', helpers.time_to_str(self.accessed))
        s.set(sec, 'Modified', helpers.time_to_str(self.modified))

        sec = 'Tags'
        s.add_section(sec)
        s.set(sec, 'sessions', repr(self.session_tags))
        s.set(sec, 'datasets', repr(self.dataset_tags))

        with open(self.infofile, 'w') as f:
            s.write(f)

    def access(self):
        """Update last access time and save."""
        self.accessed = datetime.now()
        self.save()

    def list_contents(self, tag_filters):
        """Get a list of directory names in this directory."""
        files = os.listdir(self.dir)
        dirs = [helpers.ds_decode(s[:-4]) for s in files if s.endswith('.dir')]
        datasets = [helpers.ds_decode(s[:-4]) for s in files if s.endswith('.csv')]

        # apply tag filters

        def include(entries, tag, tags):
            """Include only entries that have the specified tag."""
            return [e for e in entries
                    if e in tags and tag in tags[e]]

        def exclude(entries, tag, tags):
            """Exclude all entries that have the specified tag."""
            return [e for e in entries
                    if e not in tags or tag not in tags[e]]

        for tag in tag_filters:
            if tag[:1] == '-':
                tag_filter = exclude
                tag = tag[1:]
            else:
                tag_filter = include
            dirs = tag_filter(dirs, tag, self.session_tags)
            datasets = tag_filter(datasets, tag, self.dataset_tags)
        return dirs, datasets

    def list_datasets(self):
        """Get a list of dataset names in this directory."""
        files = os.listdir(self.dir)
        return [helpers.ds_decode(s[:-4]) for s in files if s.endswith('.csv')]

    def new_dataset(self, title, independents, dependents, dtype):
        num = self.counter
        self.counter += 1
        self.modified = datetime.now()

        name = '%05d - %s' % (num, title)
        dataset = Dataset(self, name, dtype, title, create=True)
        for i in independents:
            dataset.add_independent(i)
        for d in dependents:
            dataset.add_dependent(d)
        self.datasets[name] = dataset
        self.access()

        # notify listeners about the new dataset
        self.parent.onNewDataset(name, self.listeners)
        # self.parent.onNewDatasetDir((name, self.path), self.listeners)
        return dataset

    def new_matrix_dataset(self, title, size, dtype):
        num = self.counter
        self.counter += 1
        self.modified = datetime.now()
        name = '%05d - %s' % (num, title)
        dataset = Dataset(self, name, dtype, title, create=True)
        dataset.matrixrows = size[0]
        dataset.matrixcolumns = size[1]
        self.datasets[name] = dataset
        self.access()

        self.parent.onNewDataset(name, self.listeners)
        return dataset

    def open_dataset(self, name):
        # first lookup by number if necessary
        if isinstance(name, int):
            for old_name in self.list_datasets():
                num = int(old_name[:5])
                if name == num:
                    name = old_name
                    break
        # if it's still a number, we didn't find the set
        if isinstance(name, int):
            raise DatasetNotFoundError(name)

        filename = helpers.ds_encode(name)
        if not os.path.exists(os.path.join(self.dir, filename + '.csv')):
            raise DatasetNotFoundError(name)

        if name in self.datasets:
            dataset = self.datasets[name]
            dataset.access()
        else:
            # need to create a new wrapper for this dataset
            dataset = Dataset(self, name)
            self.datasets[name] = dataset
        self.access()

        return dataset

    def update_tags(self, tags, sessions, datasets):
        def update_tag_dict(tags, entries, d):
            updates = []
            for entry in entries:
                changed = False
                if entry not in d:
                    d[entry] = set()
                entry_tags = d[entry]
                for tag in tags:
                    if tag[:1] == '-':
                        # remove this tag
                        tag = tag[1:]
                        if tag in entry_tags:
                            entry_tags.remove(tag)
                            changed = True
                    elif tag[:1] == '^':
                        # toggle this tag
                        tag = tag[1:]
                        if tag in entry_tags:
                            entry_tags.remove(tag)
                        else:
                            entry_tags.add(tag)
                        changed = True
                    else:
                        # add this tag
                        if tag not in entry_tags:
                            entry_tags.add(tag)
                            changed = True
                if changed:
                    updates.append((entry, sorted(entry_tags)))
            return updates

        sess_updates = update_tag_dict(tags, sessions, self.session_tags)
        data_updates = update_tag_dict(tags, datasets, self.dataset_tags)

        self.access()
        if len(sess_updates) + len(data_updates):
            # fire a message about the new tags
            msg = (sess_updates, data_updates)
            self.parent.onTagsUpdated(msg, self.listeners)

    def get_tags(self, sessions, datasets):
        sess_tags = [(s, sorted(self.session_tags.get(s, []))) for s in sessions]
        data_tags = [(d, sorted(self.dataset_tags.get(d, []))) for d in datasets]
        return sess_tags, data_tags


class DataVault(LabradServer):
    name = 'Data Vault'

    @inlineCallbacks
    def initServer(self):
        # load configuration info from registry
        path = ['', 'Servers', self.name, 'Repository']
        nodename = util.getNodeName()
        reg = self.client.registry
        try:
            try:
                # try to load for this node
                p = reg.packet()
                p.cd(path)
                p.get(nodename, 's')
                ans = yield p.send()
            except Exception as e:
                print(e)
                # try to load default
                p = reg.packet()
                p.cd(path)
                p.get('__default__', 's')
                ans = yield p.send()
            Globals.DATADIR = ans.get
            got_location = True
        except Exception as e:
            print(e)
            try:
                print('Could not load repository location from registry.')
                print('Please enter data storage directory or hit enter to use the current directory:')
                Globals.DATADIR = input('>>>')
                if Globals.DATADIR == '':
                    Globals.DATADIR = os.path.join(os.path.split(__file__)[0], '__data__')
                if not os.path.exists(Globals.DATADIR):
                    os.makedirs(Globals.DATADIR)
                # set as default and for this node
                p = reg.packet()
                p.cd(path, True)
                p.set(nodename, Globals.DATADIR)
                p.set('__default__', Globals.DATADIR)
                yield p.send()
                print(Globals.DATADIR, "has been saved in the registry")
                print("as the data location.")
                print("To change this, stop this server,")
                print("edit the registry keys at", path)
                print("and then restart.")
            except Exception as E:
                print(E)
                print("Press [Enter] to continue...")
                input()
                sys.exit()
        # create root session
        # root = Session([''], self)
        self.root = Session([''], self)

    def initContext(self, c):
        # start in the root session
        c['path'] = ['']
        # start listening to the root session
        Session([''], self).listeners.add(c.ID)

    def expireContext(self, c):
        """Stop sending any signals to this context."""

        def remove_from_list(ls):
            if c.ID in ls:
                ls.remove(c.ID)

        for session in Session.get_all():
            remove_from_list(session.listeners)
            for dataset in session.datasets.values():
                remove_from_list(dataset.listeners)
                remove_from_list(dataset.param_listeners)
                remove_from_list(dataset.comment_listeners)
                remove_from_list(dataset.add_header_listeners)

    def get_session(self, c):
        """Get a session object for the current path."""
        return Session(c['path'], self)

    def get_dataset(self, c):
        """Get a dataset object for the current dataset."""
        if 'dataset' not in c:
            raise NoDatasetError()
        session = self.get_session(c)
        return session.datasets[c['dataset']]

    # session signals
    onNewDir = Signal(543617, 'signal: new dir', 's')
    onNewDirectory = Signal(543624, 'signal: new directory', 's')  # MK
    onNewDataset = Signal(543618, 'signal: new dataset', 's')
    onNewDatasetDir = Signal(543623, 'signal: new dataset dir', '(s,?)')  # MR
    onTagsUpdated = Signal(543622, 'signal: tags updated', '*(s*s)*(s*s)')

    # dataset signals
    onDataAvailable = Signal(543619, 'signal: data available', '')
    onNewParameterDataset = Signal(543620, 'signal: new parameter dataset', '(i, s, ?, s)')
    onNewParameter = Signal(543625, 'signal: new parameter', '')
    onNewAdditionalHeader = Signal(543626, 'signal: new additional header', '')
    onNewAdditionalHeaderDataset = Signal(543627, 'signal: new additional header dataset', '(i, s, ?, s)')
    onCommentsAvailable = Signal(543621, 'signal: comments available', '')

    @setting(6, tag_filters=['s', '*s'], include_tags='b',
             returns=['*s{subdirs}, *s{datasets}',
                      '*(s*s){subdirs}, *(s*s){datasets}'])
    def dir(self, c, tag_filters=('-trash',), include_tags=None):
        """Get subdirectories and datasets in the current directory."""
        # print 'dir:', tagFilters, includeTags
        if isinstance(tag_filters, str):
            tag_filters = [tag_filters]
        sess = self.get_session(c)
        dirs, datasets = sess.list_contents(tag_filters)
        if include_tags:
            dirs, datasets = sess.get_tags(dirs, datasets)
        return dirs, datasets

    @setting(7, path=['s{get current directory}',
                      's{change into this directory}',
                      '*s{change into each directory in sequence}',
                      'w{go up by this many directories}'],
             create='b',
             returns='*s')
    def cd(self, c, path=None, create=False):
        """Change the current directory.

        The empty string '' refers to the root directory. If the 'create' flag
        is set to true, new directories will be created as needed.
        Returns the path to the new current directory.
        """
        if path is None:
            return c['path']

        temp = c['path'][:]  # copy the current path
        if isinstance(path, int):
            if path > 0:
                temp = temp[:-path]
                if not len(temp):
                    temp = ['']
        else:
            if isinstance(path, str):
                path = [path]
            for directory in path:
                if directory == '':
                    temp = ['']
                else:
                    temp.append(directory)
                if not Session.exists(temp) and not create:
                    raise DirectoryNotFoundError(temp)
                session = Session(temp, self)  # touch the session
        if c['path'] != temp:
            # stop listening to old session and start listening to new session
            Session(c['path'], self).listeners.remove(c.ID)
            Session(temp, self).listeners.add(c.ID)
            c['path'] = temp
        return c['path']

    @setting(8, name='s', returns='*s')
    def mkdir(self, c, name):
        """Make a new subdirectory in the current directory.

        The current directory remains selected.  You must use the
        'cd' command to select the newly-created directory.
        Directory name cannot be empty.  Returns the path to the
        created directory.
        """
        if name == '':
            raise EmptyNameError(path=None)
        path = c['path'] + [name]
        self.onNewDirectory(str(path), self.root.listeners)  # MK
        if Session.exists(path):
            raise DirectoryExistsError(path)
        sess = Session(path, self)  # make the new directory
        return path

    @setting(9, name='s', independents=['*s', '*(ss)'],
             dependents=['*s', '*(sss)'], dtype='s',
             returns='(*s{path}, s{name})')
    def new(self, c, name, independents, dependents, dtype='f'):
        """Create a new Dataset.

        Independent and dependent variables can be specified either
        as clusters of strings, or as single strings.  Independent
        variables have the form (label, units) or 'label [units]'.
        Dependent variables have the form (label, legend, units)
        or 'label (legend) [units]'.  Label is meant to be an
        axis label that can be shared among traces, while legend is
        a legend entry that should be unique for each trace.
        Returns the path and name for this dataset.
        """
        if len(dtype) != 1 or dtype not in 'fs':
            raise TypeError("dtype keyword only accepts 'f' or 's'")
        session = self.get_session(c)
        dataset = session.new_dataset(name or 'untitled', independents, dependents, dtype)
        self.onNewDatasetDir((dataset.name, session.path), self.root.listeners)  # MR
        c['dataset'] = dataset.name  # not the same as name; has number prefixed
        c['filepos'] = 0  # start at the beginning
        c['commentpos'] = 0
        c['writing'] = True
        return c['path'], c['dataset']

    @setting(73, name='s', dtype='s', size='*i', returns='(*s{path}, s{name})')
    def new_matrix(self, c, name, size, dtype):
        """Create a new Matrix dataset

        the size specifies dimensions [row, column]
        """
        if len(dtype) != 1 or dtype not in 'fs':
            raise TypeError("dtype keyword only accepts 'f' or 's'")
        session = self.get_session(c)
        dataset = session.new_matrix_dataset(name or 'untitled', size, dtype)
        self.onNewDatasetDir((dataset.name, session.path), self.root.listeners)  # MR
        c['dataset'] = dataset.name  # not the same as name; has number prefixed
        c['filepos'] = 0  # start at the beginning
        c['commentpos'] = 0
        c['writing'] = True
        return c['path'], c['dataset']

    @setting(10, name=['s', 'w'], returns='(*s{path}, s{name})')
    def open(self, c, name):
        """Open a Dataset for reading.

        You can specify the dataset by name or number.
        Returns the path and name for this dataset.
        """
        session = self.get_session(c)
        dataset = session.open_dataset(name)
        c['dataset'] = dataset.name  # not the same as name; has number prefixed
        c['filepos'] = 0
        c['commentpos'] = 0
        c['writing'] = False
        dataset.keep_streaming(c.ID, 0)
        dataset.keep_streaming_comments(c.ID, 0)
        return c['path'], c['dataset']

    @setting(11, name=['s', 'w'], returns='(*s{path}, s{name})')
    def open_appendable(self, c, name):
        """Open a Dataset for reading and appending.

        You can specify the dataset by name or number.
        Returns the path and name for this dataset.
        """
        session = self.get_session(c)
        dataset = session.open_dataset(name)
        c['dataset'] = dataset.name  # not the same as name; has number prefixed
        c['filepos'] = 0
        c['commentpos'] = 0
        c['writing'] = True
        dataset.keep_streaming(c.ID, 0)
        dataset.keep_streaming_comments(c.ID, 0)
        return c['path'], c['dataset']

    @setting(20, data=['*v: add one row of data',
                       '*2v: add multiple rows of data',
                       '*s: add string of data',
                       '*2s: add multiple strings'], returns='')
    def add(self, c, data):
        """Add data to the current dataset.

        The number of elements in each row of data must be equal
        to the total number of variables in the data set
        (independents + dependents).
        """
        dataset = self.get_dataset(c)
        if not c['writing']:
            raise ReadOnlyError()
        dataset.add_data(data)

    @setting(21, limit='w', start_over='b', returns=['*2v', '*2s', '*s'])
    def get(self, c, limit=None, start_over=False):
        """Get data from the current dataset.

        Limit is the maximum number of rows of data to return, with
        the default being to return the whole dataset.  Setting the
        startOver flag to true will return data starting at the beginning
        of the dataset.  By default, only new data that has not been seen
        in this context is returned.
        """
        dataset = self.get_dataset(c)
        c['filepos'] = 0 if start_over else c['filepos']
        data, c['filepos'] = dataset.get_data(limit, c['filepos'])
        dataset.keep_streaming(c.ID, c['filepos'])
        return data

    # Add in saving camera images as a .npy with the dataset

    @setting(22, data='*i', image_size='*i', repetitions='i', filename='s', returns='')
    def save_image(self, c, data, image_size, repetitions, filename):
        """
        Save a CCD image of the open dataest to a .npy file
        """
        session = self.get_session(c)
        x_pixels, y_pixels = image_size
        data = numpy.reshape(data, (repetitions, y_pixels, x_pixels))
        image = Image(session, filename)
        image.add_data(data)

    @setting(100, returns='(*(ss){independents}, *(sss){dependents})')
    def variables(self, c):
        """Get the independent and dependent variables for the current dataset.

        Each independent variable is a cluster of (label, units).
        Each dependent variable is a cluster of (label, legend, units).
        Label is meant to be an axis label, which may be shared among several
        traces, while legend is unique to each trace.
        """
        ds = self.get_dataset(c)
        ind = [(i['label'], i['units']) for i in ds.independents]
        dep = [(d['category'], d['label'], d['units']) for d in ds.dependents]
        return ind, dep

    @setting(120, returns='*s')
    def parameters(self, c):
        """Get a list of parameter names."""
        dataset = self.get_dataset(c)
        # send a message when new parameters are added
        dataset.param_listeners.add(c.ID)
        return [par['label'] for par in dataset.parameters]

    @setting(121, 'add parameter', name='s', returns='')
    def add_parameter(self, c, name, data):
        """Add a new parameter to the current dataset."""
        dataset = self.get_dataset(c)
        dataset.add_parameter(name, data)

    @setting(122, 'get parameter', name='s')
    def get_parameter(self, c, name, case_sensitive=True):
        """Get the value of a parameter."""
        dataset = self.get_dataset(c)
        return dataset.get_parameter(name, case_sensitive)

    @setting(123, 'get parameters')
    def get_parameters(self, c):
        """Get all parameters.

        Returns a cluster of (name, value) clusters, one for each parameter.
        If the set has no parameters, nothing is returned (since empty clusters
        are not allowed).
        """
        dataset = self.get_dataset(c)
        names = [par['label'] for par in dataset.parameters]
        params = tuple((name, dataset.get_parameter(name)) for name in names)
        # send a message when new parameters are added
        dataset.param_listeners.add(c.ID)
        if len(params):
            return params

    @inlineCallbacks
    def read_pars_int(self, c, ctx, dataset, curdirs, subdirs=None):
        p = self.client.registry.packet(context=ctx)
        todo = []
        for curdir, curcontent in curdirs:
            if len(curdir) > 0:
                p.cd(curdir)
            for key in curcontent[1]:
                p.get(key, key=(False, tuple(curdir + [key])))
            if subdirs is not None:
                if isinstance(subdirs, list):
                    for folder in curcontent[0]:
                        if folder in subdirs:
                            p.cd(folder)
                            p.dir(key=(True, tuple(curdir + [folder])))
                            p.cd(1)
                elif subdirs != 0:
                    for folder in curcontent[0]:
                        p.cd(folder)
                        p.dir(key=(True, tuple(curdir + [folder])))
                        p.cd(1)
            if len(curdir) > 0:
                p.cd(len(curdir))
        ans = yield p.send()
        if isinstance(subdirs, list):
            subdirs = -1
        else:
            if (subdirs is not None) and (subdirs > 0):
                subdirs -= 1
        for key in sorted(ans.settings.keys()):
            item = ans[key]
            if isinstance(key, tuple):
                if key[0]:
                    curdirs = [(list(key[1]), item)]
                    yield self.read_pars_int(c, ctx, dataset, curdirs, subdirs)
                else:
                    dataset.add_parameter(' -> '.join(key[1]), item, save_now=False)

    @setting(125, 'import parameters',
             subdirs=[' : Import current directory',
                      'w: Include this many levels of subdirectories (0=all)',
                      '*s: Include these subdirectories'],
             returns='')
    def import_parameters(self, c, subdirs=None):
        """Reads all entries from the current registry directory, optionally
        including subdirectories, as parameters into the current dataset."""
        dataset = self.get_dataset(c)
        ctx = self.client.context()
        p = self.client.registry.packet(context=ctx)
        p.duplicate_context(c.ID)
        p.dir()
        ans = yield p.send()
        curdirs = [([], ans.dir)]
        if subdirs == 0:
            subdirs = -1
        yield self.read_pars_int(c, ctx, dataset, curdirs, subdirs)
        dataset.save()  # make sure the new parameters get saved

    @setting(126, 'add parameter over write', name='s', returns='')
    def add_parameter_over_write(self, c, name, data):
        """Add a new parameter to the current dataset."""
        dataset = self.get_dataset(c)
        dataset.add_parameter_overwrite(name, data)

    @setting(127, 'wait for parameter', name='s', timeout='i')
    def wait_for_parameter(self, c, name, timeout=60):
        """Wait for parameter"""
        dataset = self.get_dataset(c)
        d = Deferred()
        call_id = reactor.callLater(timeout, dataset.parameter_timeout, name, d)
        dataset.timeOutCallIDs[d] = call_id
        try:
            dataset.deferredParameterDict[name].append(d)
        except KeyError:
            dataset.deferredParameterDict[name] = [d]
        result = yield d
        returnValue(result)

    @setting(200, 'add comment', comment=['s'], user=['s'], returns=[''])
    def add_comment(self, c, comment, user='anonymous'):
        """Add a comment to the current dataset."""
        dataset = self.get_dataset(c)
        return dataset.add_comment(user, comment)

    @setting(201, 'get comments', limit=['w'], start_over=['b'],
             returns=['*(t, s{user}, s{comment})'])
    def get_comments(self, c, limit=None, start_over=False):
        """Get comments for the current dataset."""
        dataset = self.get_dataset(c)
        c['commentpos'] = 0 if start_over else c['commentpos']
        comments, c['commentpos'] = dataset.get_comments(limit, c['commentpos'])
        dataset.keep_streaming_comments(c.ID, c['commentpos'])
        return comments

    @setting(300, 'update tags', tags=['s', '*s'], dirs=['s', '*s'],
             datasets=['s', '*s'], returns='')
    def update_tags(self, c, tags, dirs, datasets=None):
        """Update the tags for the specified directories and datasets.

        If a tag begins with a minus sign '-' then the tag (everything
        after the minus sign) will be removed.  If a tag begins with '^'
        then it will be toggled from its current state for each entry
        in the list. Otherwise, it will be added.

        The directories and datasets must be in the current directory.
        """
        if isinstance(tags, str):
            tags = [tags]
        if isinstance(dirs, str):
            dirs = [dirs]
        if datasets is None:
            datasets = [self.get_dataset(c)]
        elif isinstance(datasets, str):
            datasets = [datasets]
        sess = self.get_session(c)
        sess.update_tags(tags, dirs, datasets)

    @setting(301, 'get tags', dirs=['s', '*s'], datasets=['s', '*s'],
             returns='*(s*s)*(s*s)')
    def get_tags(self, c, dirs, datasets):
        """Get tags for directories and datasets in the current dir."""
        sess = self.get_session(c)
        if isinstance(dirs, str):
            dirs = [dirs]
        if isinstance(datasets, str):
            datasets = [datasets]
        return sess.get_tags(dirs, datasets)

    @setting(128, 'add additional header', header_name='s', name='s', returns='')
    def add_additional_header(self, c, header_name, name, data):
        """
        Add a new additional header to the current dataset.
        header_name will be converted to lower case.
        """
        dataset = self.get_dataset(c)
        dataset.add_additional_header(header_name, name, data)

    @setting(129, returns='*(ss)')
    def additional_headers(self, c):
        """Get a list of additional header (header_name, name) tuples."""
        dataset = self.get_dataset(c)
        # send a message when new additional headers are added
        dataset.add_header_listeners.add(c.ID)
        additional_headers = []
        for header in dataset.additional_headers:
            for item in dataset.additional_headers[header]:
                additional_headers.append((header, item["label"]))
        return additional_headers

    @setting(130, 'get additional header', header_name='s', name='s')
    def get_additional_header(self, c, header_name, name, case_sensitive=True):
        """Get the value of an additional header."""
        dataset = self.get_dataset(c)
        return dataset.get_additional_header(header_name, name, case_sensitive)

    @setting(131, 'get additional headers')
    def get_additional_headers(self, c):
        """Get all additional headers.

        Returns a cluster of (header_name, name, value) clusters, one for each header item.
        If the set has no additional headers, nothing is returned (since empty clusters
        are not allowed).
        """
        dataset = self.get_dataset(c)
        additional_headers = ()
        for header in dataset.additional_headers:
            for item in dataset.additional_headers[header]:
                additional_headers += ((header, item["label"], item["data"]),)
        # send a message when new parameters are added
        dataset.add_header_listeners.add(c.ID)
        if len(additional_headers) > 0:
            return additional_headers


__server__ = DataVault()

if __name__ == '__main__':
    from labrad import util

    util.runServer(__server__)
