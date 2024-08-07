import os
from datetime import datetime
from configparser import ConfigParser as SafeConfigParser

from twisted.internet import reactor

import helpers
from globals import Globals
from errors import *

try:
    import numpy
    useNumpy = True
except ImportError:
    numpy = False
    print("Numpy not imported.  The DataVault will operate, but will be slower.")
    useNumpy = False


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
        file_base = os.path.join(session.dir, helpers.ds_encode(name))
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
        self.created = helpers.time_from_str(s.get(gen, 'Created'))
        self.accessed = helpers.time_from_str(s.get(gen, 'Accessed'))
        self.modified = helpers.time_from_str(s.get(gen, 'Modified'))
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
                return helpers.time_from_str(time), user, comment

            count = s.getint(gen, 'Comments')
            self.comments = [get_comment(i) for i in range(count)]
        else:
            self.comments = []

    def save(self):
        s = SafeConfigParser()

        sec = 'General'
        s.add_section(sec)
        s.set(sec, 'DType', self.dtype)
        s.set(sec, 'Created', helpers.time_to_str(self.created))
        s.set(sec, 'Accessed', helpers.time_to_str(self.accessed))
        s.set(sec, 'Modified', helpers.time_to_str(self.modified))
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
            time = helpers.time_to_str(time)
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
            self._fileTimeoutCall = reactor.callLater(Globals.FILE_TIMEOUT, self._file_timeout)
        else:
            self._fileTimeoutCall.reset(Globals.FILE_TIMEOUT)
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
            self._dataTimeoutCall = reactor.callLater(Globals.DATA_TIMEOUT, self._data_timeout)
        else:
            self._dataTimeoutCall.reset(Globals.DATA_TIMEOUT)
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
            f.write(', '.join(Globals.DATA_FORMAT % v for v in row) + '\n')
        f.flush()

    def add_independent(self, label):
        """Add an independent variable to this dataset."""
        if isinstance(label, tuple):
            label, units = label
        else:
            label, units = helpers.parse_independent(label)
        d = dict(label=label, units=units)
        self.independents.append(d)
        self.save()

    def add_dependent(self, label):
        """Add a dependent variable to this dataset."""
        if isinstance(label, tuple):
            label, legend, units = label
        else:
            label, legend, units = helpers.parse_dependent(label)
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
            self._dataTimeoutCall = reactor.callLater(Globals.DATA_TIMEOUT, self._data_timeout)
        else:
            self._dataTimeoutCall.reset(Globals.DATA_TIMEOUT)
        return self._data

    def _set_data(self, data):
        self._data = data

    # noinspection PyTypeChecker
    data = property(_get_data, _set_data)

    def _save_data(self, data):
        def _save(file, dat):
            if self.dtype == 'float':
                numpy.savetxt(f, data, fmt=Globals.DATA_FORMAT, delimiter=',')
            if self.dtype == 'string':
                numpy.savetxt(f, data, fmt=Globals.STRING_FORMAT, delimiter=',')

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

