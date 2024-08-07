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

from configparser import ConfigParser as SafeConfigParser
import os
import re
import sys
from datetime import datetime

from errors import *

try:
    import numpy

    print("Numpy imported.")
    useNumpy = True
except ImportError:
    numpy = False
    print("Numpy not imported.  The DataVault will operate, but will be slower.")
    useNumpy = False

# TODO: tagging
# - search globally (or in some subtree of sessions) for matching tags
#     - this is the least common case, and will be an expensive operation
#     - don't worry too much about optimizing this
#     - since we won't bother optimizing the global search case, we can store
#       tag information in the session

# location of repository will get loaded from the registry
DATADIR = None
PRECISION = 15  # digits of precision to use when saving data
DATA_FORMAT = '%%.%dG' % PRECISION
STRING_FORMAT = '%s'
FILE_TIMEOUT = 60  # how long to keep datafiles open if not accessed
DATA_TIMEOUT = 300  # how long to keep data in memory if not accessed
TIME_FORMAT = '%Y-%m-%d, %H:%M:%S'

# filename translation

encodings = [
    ('%', '%p'),
    ('/', '%f'),
    ('\\', '%b'),
    (':', '%c'),
    ('*', '%a'),
    ('?', '%q'),
    ('"', '%r'),
    ('<', '%l'),
    ('>', '%g'),
    ('|', '%v')
]


def ds_encode(name: str) -> str:
    for char, code in encodings:
        name = name.replace(char, code)
    return name


def ds_decode(name: str) -> str:
    for char, code in encodings[1:] + encodings[0:1]:
        name = name.replace(code, char)
    return name


def file_dir(path) -> os.path:
    # noinspection PyTypeChecker
    return os.path.join(DATADIR, *[ds_encode(d) + '.dir' for d in path[1:]])


# time formatting

def time_to_str(t: datetime) -> str:
    return t.strftime(TIME_FORMAT)


def time_from_str(s: str) -> datetime:
    return datetime.strptime(s, TIME_FORMAT)


# variable parsing
re_label = re.compile(r'^([^\[(]*)')  # matches up to the first [ or (
re_legend = re.compile(r'\((.*)\)')  # matches anything inside ()
re_units = re.compile(r'\[(.*)]')  # matches anything inside [ ]


def get_match(pat, s, default=None):
    matches = re.findall(pat, s)
    if len(matches) == 0:
        if default is None:
            raise Exception("Cannot parse '%s'." % s)
        return default
    return matches[0].strip()


def parse_independent(s):
    label = get_match(re_label, s)
    units = get_match(re_units, s, '')
    return label, units


def parse_dependent(s):
    label = get_match(re_label, s)
    legend = get_match(re_legend, s, '')
    units = get_match(re_units, s, '')
    return label, legend, units


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
        return os.path.exists(file_dir(path))

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
        self.dir = file_dir(path)
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
        self.created = time_from_str(s.get(sec, 'Created'))
        self.accessed = time_from_str(s.get(sec, 'Accessed'))
        self.modified = time_from_str(s.get(sec, 'Modified'))

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
        s.set(sec, 'Created', time_to_str(self.created))
        s.set(sec, 'Accessed', time_to_str(self.accessed))
        s.set(sec, 'Modified', time_to_str(self.modified))

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
        dirs = [ds_decode(s[:-4]) for s in files if s.endswith('.dir')]
        datasets = [ds_decode(s[:-4]) for s in files if s.endswith('.csv')]

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
        return [ds_decode(s[:-4]) for s in files if s.endswith('.csv')]

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

        filename = ds_encode(name)
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


class Image(object):
    def __init__(self, session, filename):
        """
        session.dir is the dataset number to which this image should be attached
        """
        self.filename = os.path.join(session.dir, filename + '.npy')

    def add_data(self, data):
        fi = open(self.filename, 'ab')
        numpy.save(fi, data)
        fi.close()


class Dataset:
    def __init__(self, session, name, dtype=None, title=None, num=None,
                 create=False):
        self.parent = session.parent
        self.name = name
        self.session = session  # MK
        file_base = os.path.join(session.dir, ds_encode(name))
        self.datafile = file_base + '.csv'
        self.infofile = file_base + '.ini'
        # noinspection PyStatementEffect
        self.file  # create the datafile, but don't do anything with it
        self.listeners = set()  # contexts that want to hear about added data
        self.param_listeners = set()
        self.add_header_listeners = set()
        self.comment_listeners = set()
        self.deferredParameterDict = {}  # MK
        self.timeOutCallIDs = {}
        if dtype:
            dtype = 'float' if dtype in 'f' else 'string'

        if create:
            self.dtype = dtype
            self.title = title
            self.created = self.accessed = self.modified = datetime.now()
            self.independents = []
            self.dependents = []
            self.parameters = []
            self.comments = []
            self.matrixrows = []
            self.matrixcolumns = []
            self.additional_headers = {}
            self.save()
        else:
            self.load()
            self.access()

    def load(self):
        s = SafeConfigParser()
        s.read(self.infofile)

        gen = 'General'
        self.dtype = s.get(gen, 'DType')
        self.title = s.get(gen, 'Title', raw=True)
        self.created = time_from_str(s.get(gen, 'Created'))
        self.accessed = time_from_str(s.get(gen, 'Accessed'))
        self.modified = time_from_str(s.get(gen, 'Modified'))
        non_additional_header_names = ["dtype", "title", "created", "accessed",
                                       "modified", "independent", "dependent",
                                       "parameters", "comments"]
        additional_header_names = [header for header in s.options("General")
                                   if header not in non_additional_header_names]

        def get_ind(i):
            sec = 'Independent %d' % (i + 1)
            label = s.get(sec, 'Label', raw=True)
            units = s.get(sec, 'Units', raw=True)
            return dict(label=label, units=units)

        count = s.getint(gen, 'Independent')
        self.independents = [get_ind(i) for i in range(count)]

        def get_dep(i):
            sec = 'Dependent %d' % (i + 1)
            label = s.get(sec, 'Label', raw=True)
            units = s.get(sec, 'Units', raw=True)
            categ = s.get(sec, 'Category', raw=True)
            return dict(label=label, units=units, category=categ)

        count = s.getint(gen, 'Dependent')
        self.dependents = [get_dep(i) for i in range(count)]

        def get_par(i):
            sec = 'Parameter %d' % (i + 1)
            label = s.get(sec, 'Label', raw=True)
            # TODO: big security hole! eval can execute arbitrary code
            data = types.evalLRData(s.get(sec, 'Data', raw=True))
            return dict(label=label, data=data)

        count = s.getint(gen, 'Parameters')
        self.parameters = [get_par(i) for i in range(count)]

        def get_addi_header(header_name, i):
            sec = header_name + ' %d' % (i + 1)
            label = s.get(sec, 'Label', raw=True)
            # TODO: big security hole! eval can execute arbitrary code
            data = types.evalLRData(s.get(sec, 'Data', raw=True))
            return dict(label=label, data=data)

        self.additional_headers = {}
        for header in additional_header_names:
            count = s.getint(gen, header)
            self.additional_headers[header] = [get_addi_header(header, i) for i in range(count)]

        # get comments if they're there
        if s.has_section('Comments'):
            def get_comment(i):
                sec = 'Comments'
                time, user, comment = eval(s.get(sec, 'c%d' % i, raw=True))
                return time_from_str(time), user, comment

            count = s.getint(gen, 'Comments')
            self.comments = [get_comment(i) for i in range(count)]
        else:
            self.comments = []

    def save(self):
        s = SafeConfigParser()

        sec = 'General'
        s.add_section(sec)
        s.set(sec, 'DType', self.dtype)
        s.set(sec, 'Created', time_to_str(self.created))
        s.set(sec, 'Accessed', time_to_str(self.accessed))
        s.set(sec, 'Modified', time_to_str(self.modified))
        s.set(sec, 'Title', self.title)
        s.set(sec, 'Independent', repr(len(self.independents)))
        s.set(sec, 'Dependent', repr(len(self.dependents)))
        s.set(sec, 'Parameters', repr(len(self.parameters)))
        s.set(sec, 'Comments', repr(len(self.comments)))
        for header in self.additional_headers:
            s.set(sec, header, repr(len(self.additional_headers[header])))

        for i, ind in enumerate(self.independents):
            sec = 'Independent %d' % (i + 1)
            s.add_section(sec)
            s.set(sec, 'Label', ind['label'])
            s.set(sec, 'Units', ind['units'])

        for i, dep in enumerate(self.dependents):
            sec = 'Dependent %d' % (i + 1)
            s.add_section(sec)
            s.set(sec, 'Label', dep['label'])
            s.set(sec, 'Units', dep['units'])
            s.set(sec, 'Category', dep['category'])

        for i, par in enumerate(self.parameters):
            sec = 'Parameter %d' % (i + 1)
            s.add_section(sec)
            s.set(sec, 'Label', par['label'])
            # TODO: smarter saving here, since eval'ing is insecure
            s.set(sec, 'Data', repr(par['data']))

        for header in self.additional_headers:
            values = self.additional_headers[header]
            for i, value in enumerate(values):
                sec = header + ' %d' % (i + 1)
                s.add_section(sec)
                s.set(sec, 'Label', value['label'])
                s.set(sec, 'Data', repr(value['data']))

        sec = 'Comments'
        s.add_section(sec)
        for i, (time, user, comment) in enumerate(self.comments):
            time = time_to_str(time)
            s.set(sec, 'c%d' % i, repr((time, user, comment)))

        with open(self.infofile, 'w') as f:
            s.write(f)

    def access(self):
        """Update time of last access for this dataset."""
        self.accessed = datetime.now()
        self.save()

    @property
    def file(self):
        """Open the datafile on demand.

        The file is also scheduled to be closed
        if it has not accessed for a while.
        """
        if not hasattr(self, '_file'):
            self._file = open(self.datafile, 'a+')  # append data
            self._fileTimeoutCall = reactor.callLater(FILE_TIMEOUT, self._file_timeout)
        else:
            self._fileTimeoutCall.reset(FILE_TIMEOUT)
        return self._file

    def _file_timeout(self):
        self._file.close()
        del self._file
        del self._fileTimeoutCall

    def _file_size(self):
        """Check the file size of our datafile."""
        # does this include the size before the file has been flushed to disk?
        return os.fstat(self.file.fileno()).st_size

    @property
    def data(self):
        """Read data from file on demand.

        The data is scheduled to be cleared from memory unless accessed."""
        if not hasattr(self, '_data'):
            self._data = []
            self._datapos = 0
            self._dataTimeoutCall = reactor.callLater(DATA_TIMEOUT, self._data_timeout)
        else:
            self._dataTimeoutCall.reset(DATA_TIMEOUT)
        f = self.file
        f.seek(self._datapos)
        lines = f.readlines()
        self._data.extend([float(n) for n in line.split(',')] for line in lines)
        self._datapos = f.tell()
        return self._data

    def _data_timeout(self):
        del self._data
        del self._datapos
        del self._dataTimeoutCall

    def _save_data(self, data):
        f = self.file
        for row in data:
            f.write(', '.join(DATA_FORMAT % v for v in row) + '\n')
        f.flush()

    def add_independent(self, label):
        """Add an independent variable to this dataset."""
        if isinstance(label, tuple):
            label, units = label
        else:
            label, units = parse_independent(label)
        d = dict(label=label, units=units)
        self.independents.append(d)
        self.save()

    def add_dependent(self, label):
        """Add a dependent variable to this dataset."""
        if isinstance(label, tuple):
            label, legend, units = label
        else:
            label, legend, units = parse_dependent(label)
        d = dict(category=label, label=legend, units=units)
        self.dependents.append(d)
        self.save()

    def add_parameter(self, name, data, save_now=True):
        for p in self.parameters:
            if p['label'] == name:
                raise ParameterInUseError(name)
        d = dict(label=name, data=data)
        self.parameters.append(d)
        if save_now:
            self.save()

        # notify all listening contexts
        self.parent.onNewParameter(None, self.param_listeners)
        self.parent.onNewParameterDataset((int(self.name[0:5]), self.name[8:len(self.name)], self.session.path, name),
                                          self.parent.root.listeners)
        self.param_listeners = set()
        return name

    # MK
    def add_parameter_overwrite(self, name, data, save_now=True):
        done = False
        for p in self.parameters:
            if p['label'] == name:
                p['data'] = data
                done = True
        if not done:
            d = dict(label=name, data=data)
            self.parameters.append(d)
        if save_now:
            self.save()
        if name in self.deferredParameterDict.keys():
            for dParam in self.deferredParameterDict[name][:]:
                self.timeOutCallIDs[dParam].cancel()  # cancel the callLater!
                self.timeOutCallIDs.pop(dParam)
                dParam.callback(data)
                # delete the deferredLIST
                self.deferredParameterDict[name].pop(0)

        # notify all listening contexts
        self.parent.onNewParameter(None, self.param_listeners)
        self.param_listeners = set()
        return name

    def parameter_timeout(self, name, d_param):
        # call back the associated parameter deferred and remove it from the list!
        for d_parameter in self.deferredParameterDict[name]:
            if d_parameter == d_param:
                d_param.callback(False)
                self.deferredParameterDict[name].remove(d_param)

    def get_parameter(self, name, case_sensitive=True):
        for p in self.parameters:
            if case_sensitive:
                if p['label'] == name:
                    return p['data']
            else:
                if p['label'].lower() == name.lower():
                    return p['data']
        raise BadParameterError(name)

    def add_data(self, data):
        varcount = len(self.independents) + len(self.dependents)
        if not len(data) or not isinstance(data[0], list):
            data = [data]
        if len(data[0]) != varcount:
            raise BadDataError(varcount, len(data[0]))

        # append the data to the file
        self._save_data(data)

        # notify all listening contexts
        self.parent.onDataAvailable(None, self.listeners)
        self.listeners = set()

    def get_data(self, limit, start):
        if limit is None:
            data = self.data[start:]
        else:
            data = self.data[start:start + limit]
        return data, start + len(data)

    def keep_streaming(self, context, pos):
        if pos < len(self.data):
            if context in self.listeners:
                self.listeners.remove(context)
            self.parent.onDataAvailable(None, context)
        else:
            self.listeners.add(context)

    def add_comment(self, user, comment):
        self.comments.append((datetime.now(), user, comment))
        self.save()

        # notify all listening contexts
        self.parent.onCommentsAvailable(None, self.comment_listeners)
        self.comment_listeners = set()

    def get_comments(self, limit, start):
        if limit is None:
            comments = self.comments[start:]
        else:
            comments = self.comments[start:start + limit]
        return comments, start + len(comments)

    def keep_streaming_comments(self, context, pos):
        if pos < len(self.comments):
            if context in self.comment_listeners:
                self.comment_listeners.remove(context)
            self.parent.onCommentsAvailable(None, context)
        else:
            self.comment_listeners.add(context)

    def add_additional_header(self, header_name, name, data, save_now=True):
        header_name = header_name.lower()
        if header_name not in self.additional_headers:
            self.additional_headers[header_name] = []
        for p in self.additional_headers[header_name]:
            if p['label'] == name:
                raise AdditionalHeaderInUseError(header_name, name)
        d = dict(label=name, data=data)
        self.additional_headers[header_name].append(d)
        if save_now:
            self.save()

        # notify all listening contexts
        self.parent.onNewAdditionalHeader(None, self.add_header_listeners)
        self.parent.onNewAdditionalHeaderDataset((int(self.name[0:5]),
                                                  self.name[8:len(self.name)],
                                                  self.session.path,
                                                  name),
                                                 self.parent.root.listeners)
        self.add_header_listeners = set()
        return name

    def get_additional_header(self, header_name, name, case_sensitive=True):
        for header in self.additional_headers:
            for item in self.additional_headers[header]:
                if case_sensitive:
                    if item['label'] == name:
                        return item['data']
                else:
                    if item['label'].lower() == name.lower():
                        return item['data']
        raise BadAdditionalHeaderError(header_name, name)


class NumpyDataset(Dataset):

    def _get_data(self):
        """Read data from file on demand.

        The data is scheduled to be cleared from memory unless accessed."""
        if not hasattr(self, '_data'):
            def _get(f):
                if self.dtype == 'float':
                    return numpy.loadtxt(self.file.name, delimiter=',')
                if self.dtype == 'string':
                    return numpy.loadtxt(self.file.name, delimiter=',', dtype=str)

            try:
                # if the file is empty, this line can barf in certain versions
                # of numpy.  Clearly, if the file does not exist on disk, this
                # will be the case.  Even if the file exists on disk, we must
                # check its size
                if self._file_size() > 0:
                    self._data = _get(self.file.name)
                else:
                    self._data = numpy.array([[]])
                if len(self._data.shape) == 1:
                    self._data.shape = (1, len(self._data))
            except ValueError:
                # no data saved yet
                # this error is raised by numpy <=1.2
                self._data = numpy.array([[]])
            except IOError:
                # no data saved yet
                # this error is raised by numpy 1.3
                self.file.seek(0)
                self._data = numpy.array([[]])
            self._dataTimeoutCall = reactor.callLater(DATA_TIMEOUT, self._data_timeout)
        else:
            self._dataTimeoutCall.reset(DATA_TIMEOUT)
        return self._data

    def _set_data(self, data):
        self._data = data

    # noinspection PyTypeChecker
    data = property(_get_data, _set_data)

    def _save_data(self, data):
        def _save(file, dat):
            if self.dtype == 'float':
                numpy.savetxt(f, data, fmt=DATA_FORMAT, delimiter=',')
            if self.dtype == 'string':
                numpy.savetxt(f, data, fmt=STRING_FORMAT, delimiter=',')

        f = self.file
        _save(f, data)
        f.flush()

    def _data_timeout(self):
        del self._data
        del self._dataTimeoutCall

    def add_data(self, data):
        varcount = 0
        if self.independents:
            varcount = len(self.independents) + len(self.dependents)
        if self.matrixcolumns:
            varcount = self.matrixcolumns
        # reshape single row
        if len(data.shape) == 1:
            data.shape = (1, data.size)

        # check row length
        if data.shape[-1] != varcount:
            raise BadDataError(varcount, data.shape[-1])

        # append data to in-memory data
        if self.data.size > 0:
            self.data = numpy.vstack((self.data, data))
        else:
            self.data = data

        # append data to file
        self._save_data(data)

        # notify all listening contexts
        self.parent.onDataAvailable(None, self.listeners)
        self.listeners = set()

    def get_data(self, limit, start):
        if limit is None:
            data = self.data[start:]
        else:
            data = self.data[start:start + limit]
        # nrows should be zero for an empty row
        nrows = len(data) if data.size > 0 else 0
        return data, start + nrows

    def keep_streaming(self, context, pos):
        # cheesy hack: if pos == 0, we only need to check whether
        # the filesize is nonzero
        if pos == 0:
            more = os.path.getsize(self.datafile) > 0
        else:
            nrows = len(self.data) if self.data.size > 0 else 0
            more = pos < nrows
        if more:
            if context in self.listeners:
                self.listeners.remove(context)
            self.parent.onDataAvailable(None, context)
        else:
            self.listeners.add(context)


if useNumpy:
    Dataset = NumpyDataset


class DataVault(LabradServer):
    name = 'Data Vault'

    @inlineCallbacks
    def initServer(self):
        # load configuration info from registry
        global DATADIR
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
            DATADIR = ans.get
            got_location = True
        except Exception as e:
            print(e)
            try:
                print('Could not load repository location from registry.')
                print('Please enter data storage directory or hit enter to use the current directory:')
                DATADIR = input('>>>')
                if DATADIR == '':
                    DATADIR = os.path.join(os.path.split(__file__)[0], '__data__')
                if not os.path.exists(DATADIR):
                    os.makedirs(DATADIR)
                # set as default and for this node
                p = reg.packet()
                p.cd(path, True)
                p.set(nodename, DATADIR)
                p.set('__default__', DATADIR)
                yield p.send()
                print(DATADIR, "has been saved in the registry")
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
