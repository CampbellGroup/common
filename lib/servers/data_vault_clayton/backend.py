"""
Contains all data file objects used by the server and utilities used to create/open them.
"""
import os
import h5py
import base64
import datetime
import numpy as np

from time import time
from sys import maxsize
from collections import namedtuple

from . import errors, util
from labrad import types
from twisted.internet import reactor

# Data types for variable defintions
Independent = namedtuple('Independent', ['label', 'shape', 'datatype', 'unit'])
Dependent = namedtuple('Dependent', ['label', 'legend', 'shape', 'datatype', 'unit'])

TIME_FORMAT = '%Y-%m-%d, %H:%M:%S'
PRECISION = 12  # digits of precision to use when saving data
DATA_FORMAT = '%%.%dG' % PRECISION
FILE_TIMEOUT_SEC = 60  # how long to keep datafiles open if not accessed
DATA_TIMEOUT = 300  # how long to keep data in memory if not accessed
DATA_URL_PREFIX = 'data:application/labrad;base64,'
# todo: break backend up into general stuff (e.g. selfclosingfile, helper functions) and file format implementations
# todo: note somewhere that versioning uses semantic versioning
# todo: document versions and differences
# todo: if artiq dataset just has 1D, create dependent variables for down
# todo: why are certain functions defined here again, as well as in __init__?


def time_to_str(t):
    return t.strftime(TIME_FORMAT)


def time_from_str(s):
    return datetime.datetime.strptime(s, TIME_FORMAT)


def labrad_urlencode(data):
    if hasattr(types, 'FlatData'):
        # pylabrad 0.95+
        flat_data = types.flatten(data)
        flat_cluster = types.flatten((str(flat_data.tag), flat_data.bytes), 'sy')
        all_bytes = flat_cluster.bytes
    else:
        data_bytes, t = types.flatten(data)
        all_bytes, _ = types.flatten((str(t), data_bytes), 'ss')
    data_url = DATA_URL_PREFIX + (base64.urlsafe_b64encode(all_bytes)).decode()
    return data_url


def labrad_urldecode(data_url):
    if data_url.startswith(DATA_URL_PREFIX):
        # decode parameter data from dataurl
        all_bytes = base64.urlsafe_b64decode(data_url[len(DATA_URL_PREFIX):])
        t, data_bytes = types.unflatten(all_bytes, 'ss')
        # ensure data_bytes is of type bytes
        if isinstance(data_bytes, str):
            data_bytes = data_bytes.encode()
        return types.unflatten(data_bytes, t)
    else:
        raise ValueError("Trying to labrad_urldecode data that doesn't start "
                         "with prefix: {}".format(DATA_URL_PREFIX))


class SelfClosingFile(object):
    """
    A container for a file object that manages the underlying file handle.

    The file will be opened on demand when this container is called, then
    closed automatically if not accessed within a specified timeout.
    """

    def __init__(self, opener=open, open_args=(), open_kw=None,
                 timeout=FILE_TIMEOUT_SEC, touch=True, reactor=reactor):
        if open_kw is None:
            open_kw = dict()
        self.opener = opener
        self.open_args = open_args
        self.open_kw = open_kw
        self.timeout = timeout
        self.callbacks = []
        self.reactor = reactor
        if touch:
            self.__call__()

    def __call__(self):
        """
        Start timeout-polling the file for closing.
        Runs when an instance is called without arguments
        (e.g. e = Example, e())
        """
        # open the file if we don't already have one
        if not hasattr(self, '_file'):
            self._file = self.opener(*self.open_args, **self.open_kw)
            # begin the countdown if called after exceeding the timeout
            self._fileTimeoutCall = self.reactor.callLater(self.timeout, self._file_timeout)
        # otherwise, reset the timer
        else:
            self._fileTimeoutCall.reset(self.timeout)
        return self._file

    def _file_timeout(self):
        """
        Run all cleanup callbacks, close the file, and delete timeout functions.
        """
        for callback in self.callbacks:
            callback(self)
        self._file.close()
        del self._file
        del self._fileTimeoutCall

    def size(self):
        return os.fstat(self().fileno()).st_size

    def on_close(self, callback):
        """
        Calls callback *before* the file is closed.
        """
        self.callbacks.append(callback)


# INI & CSV FILES
class IniData(object):
    """
    Handles dataset metadata stored in INI files.

    This is used via subclassing mostly out of laziness: this was the
    easy way to separate it from the code that messes with the actual
    data storage so that the data storage can be modified to use HDF5
    and complex data structures.  Once the HDF5 stuff is finished,
    this can be changed to use composition rather than inheritance.
    This provides the load() and save() methods to read and write the
    INI file as well as accessors for all the metadata attributes.
    """

    def load(self):
        s = util.DVSafeConfigParser()
        s.read(self.infofile)

        gen = 'General'
        self.title = s.get(gen, 'Title', raw=True)
        self.created = time_from_str(s.get(gen, 'Created'))
        self.accessed = time_from_str(s.get(gen, 'Accessed'))
        self.modified = time_from_str(s.get(gen, 'Modified'))

        def get_ind(i):
            sec = 'Independent {}'.format(i + 1)
            label = s.get(sec, 'Label', raw=True)
            units = s.get(sec, 'Units', raw=True)
            return Independent(label=label, shape=(1,), datatype='v', unit=units)

        count = s.getint(gen, 'Independent')
        self.independents = [get_ind(i) for i in range(count)]

        def get_dep(i):
            sec = 'Dependent {}'.format(i + 1)
            label = s.get(sec, 'Label', raw=True)
            units = s.get(sec, 'Units', raw=True)
            categ = s.get(sec, 'Category', raw=True)
            return Dependent(label=categ, legend=label, shape=(1,), datatype='v', unit=units)

        count = s.getint(gen, 'Dependent')
        self.dependents = [get_dep(i) for i in range(count)]

        self.cols = len(self.independents + self.dependents)

        def get_par(i):
            sec = 'Parameter {}'.format(i + 1)
            label = s.get(sec, 'Label', raw=True)
            raw = s.get(sec, 'Data', raw=True)
            if raw.startswith(DATA_URL_PREFIX):
                # decode parameter data from dataurl
                data = labrad_urldecode(raw)
            else:
                # old parameters may have been saved using repr
                try:
                    data = types.evalLRData(raw)
                except RuntimeError:
                    # This is a hack to parse some very old data that seems to
                    # have been created by converting delphi data to python
                    # format. '1.#IND' was produced by old versions of the
                    # delphi labrad api when stringifying NaN.
                    if '1.#IND' in raw:
                        data = types.evalLRData(raw.replace('1.#IND', 'nan'))
                    else:
                        raise Exception('unable to parse parameter {}: {}'.format(label, raw))
            return dict(label=label, data=data)

        count = s.getint(gen, 'Parameters')
        self.parameters = [get_par(i) for i in range(count)]

        # get comments if they're there
        if s.has_section('Comments'):
            def get_comment(i):
                sec = 'Comments'
                time, user, comment = eval(s.get(sec, 'c{}'.format(i), raw=True))
                return time_from_str(time), user, comment

            count = s.getint(gen, 'Comments')
            self.comments = [get_comment(i) for i in range(count)]
        else:
            self.comments = []

    def save(self):
        s = util.DVSafeConfigParser()

        sec = 'General'
        s.add_section(sec)
        s.set(sec, 'Created', time_to_str(self.created))
        s.set(sec, 'Accessed', time_to_str(self.accessed))
        s.set(sec, 'Modified', time_to_str(self.modified))
        s.set(sec, 'Title', self.title)
        s.set(sec, 'Independent', repr(len(self.independents)))
        s.set(sec, 'Dependent', repr(len(self.dependents)))
        s.set(sec, 'Parameters', repr(len(self.parameters)))
        s.set(sec, 'Comments', repr(len(self.comments)))

        for i, ind in enumerate(self.independents):
            sec = 'Independent {}'.format(i + 1)
            s.add_section(sec)
            s.set(sec, 'Label', ind.label)
            s.set(sec, 'Units', ind.unit)

        for i, dep in enumerate(self.dependents):
            sec = 'Dependent {}'.format(i + 1)
            s.add_section(sec)
            s.set(sec, 'Label', dep.legend)
            s.set(sec, 'Units', dep.unit)
            s.set(sec, 'Category', dep.label)

        for i, par in enumerate(self.parameters):
            sec = 'Parameter {}'.format(i + 1)
            s.add_section(sec)
            s.set(sec, 'Label', par['label'])
            # encode the parameter value as a data-url
            data_url = labrad_urlencode(par['data'])
            s.set(sec, 'Data', data_url)

        sec = 'Comments'
        s.add_section(sec)
        for i, (time, user, comment) in enumerate(self.comments):
            time = time_to_str(time)
            s.set(sec, 'c{}'.format(i), repr((time, user, comment)))

        with open(self.infofile, 'w') as f:
            s.write(f)

    def initialize_info(self, title, indep, dep):
        self.title = title
        self.accessed = self.modified = self.created = datetime.datetime.now()
        self.independents = indep
        self.dependents = dep
        self.parameters = []
        self.comments = []
        self.cols = len(indep) + len(dep)

    @property
    def dtype(self):
        return np.dtype(','.join(['f8'] * self.cols))

    def access(self):
        self.accessed = datetime.datetime.now()

    def get_independents(self):
        return self.independents

    def get_dependents(self):
        return self.dependents

    def get_row_type(self):
        units = []
        for var in self.independents + self.dependents:
            units.append('v[{}]'.format(var.unit))
        type_tag = '*({})'.format(','.join(units))
        return type_tag

    def get_transpose_type(self):
        units = []
        for var in self.independents + self.dependents:
            units.append('*v[{}]'.format(var.unit))
        type_tag = '({})'.format(','.join(units))
        return type_tag

    def add_param(self, name, data):
        for p in self.parameters:
            if p['label'] == name:
                raise errors.ParameterInUseError(name)
        d = dict(label=name, data=data)
        self.parameters.append(d)

    def get_parameter(self, name, case_sensitive=True):
        for p in self.parameters:
            if case_sensitive:
                if p['label'] == name:
                    return p['data']
            else:
                if p['label'].lower() == name.lower():
                    return p['data']
        raise errors.BadParameterError(name)

    def get_param_names(self):
        return [p['label'] for p in self.parameters]

    def add_comment(self, user, comment):
        self.comments.append((datetime.datetime.now(), user, comment))

    def get_comments(self, limit, start):
        if limit is None:
            comments = self.comments[start:]
        else:
            comments = self.comments[start:start + limit]
        return comments, start + len(comments)

    def num_comments(self):
        return len(self.comments)


class CsvListData(IniData):
    """
    Data backed by a csv-formatted file.
    Stores the entire contents of the file in memory as a list or numpy array.
    """

    def __init__(self,
                 filename,
                 file_timeout=FILE_TIMEOUT_SEC,
                 data_timeout=DATA_TIMEOUT,
                 reactor=reactor):
        self.filename = filename
        self._file = SelfClosingFile(open_args=(filename, 'a+'),
                                     timeout=file_timeout,
                                     reactor=reactor)
        self.timeout = data_timeout
        self.infofile = filename[:-4] + '.ini'
        self.reactor = reactor

    @property
    def file(self):
        return self._file()

    @property
    def version(self):
        return np.asarray([1, 0, 0], np.int32)

    @property
    def data(self):
        """Read data from file on demand.

        The data is scheduled to be cleared from memory unless accessed."""
        if not hasattr(self, '_data'):
            self._data = []
            self._datapos = 0
            self._timeout_call = self.reactor.callLater(self.timeout,
                                                        self._on_timeout)
        else:
            self._timeout_call.reset(DATA_TIMEOUT)
        f = self.file
        f.seek(self._datapos)
        lines = f.readlines()
        self._data.extend([float(n) for n in line.split(',')] for line in lines)
        self._datapos = f.tell()
        return self._data

    def _on_timeout(self):
        del self._data
        del self._datapos
        del self._timeout_call

    def _save_data(self, data):
        f = self.file
        for row in data:
            # always save with dos linebreaks
            f.write(', '.join(DATA_FORMAT % v for v in row) + '\r\n')
        f.flush()

    def add_data(self, data):
        if not len(data) or not isinstance(data[0], list):
            data = [data]
        if len(data[0]) != self.cols:
            raise errors.BadDataError(self.cols, len(data[0]))

        # append the data to the file
        self._save_data(data)

    def get_data(self, limit, start, transpose, simple_only):
        if transpose:
            raise RuntimeError("Transpose specified for simple data format: not supported")
        if limit is None:
            data = self.data[start:]
        else:
            data = self.data[start:start + limit]
        return data, start + len(data)

    def has_more(self, pos):
        return pos < len(self.data)


class CsvNumpyData(CsvListData):
    """
    Data backed by a csv-formatted file.

    Stores the entire contents of the file in memory as a list or numpy array
    """

    def __init__(self, filename, reactor=reactor):
        self.filename = filename
        self._file = SelfClosingFile(open_args=(filename, 'a+'), reactor=reactor)
        self.infofile = filename[:-4] + '.ini'
        self.reactor = reactor

    @property
    def file(self):
        return self._file()

    def _get_data(self):
        """
        Read data from file on demand.
        The data is scheduled to be cleared from memory unless accessed.
        """
        if not hasattr(self, '_data'):
            try:
                # if the file is empty, this line can barf in certain versions
                # of numpy.  Clearly, if the file does not exist on disk, this
                # will be the case.  Even if the file exists on disk, we must
                # check its size
                if self._file.size() > 0:
                    self.file.seek(0)
                    self._data = np.loadtxt(self.file, delimiter=',')
                else:
                    self._data = np.array([[]])
                if len(self._data.shape) == 1:
                    self._data.shape = (1, len(self._data))
            except ValueError:
                # no data saved yet
                # this error is raised by numpy <=1.2
                self._data = np.array([[]])
            except IOError:
                # no data saved yet
                # this error is raised by numpy 1.3
                self.file.seek(0)
                self._data = np.array([[]])
            self._timeout_call = self.reactor.callLater(DATA_TIMEOUT, self._on_timeout)
        else:
            self._timeout_call.reset(DATA_TIMEOUT)
        return self._data

    def _set_data(self, data):
        self._data = data

    data = property(_get_data, _set_data)

    def _on_timeout(self):
        del self._data
        del self._timeout_call

    def _save_data(self, data):
        f = self.file
        # always save with dos linebreaks (requires numpy 1.5.0 or greater)
        np.savetxt(f, data, fmt=DATA_FORMAT, delimiter=',', newline='\r\n')
        f.flush()

    def add_data(self, data):
        # check row length
        if len(data[0]) != self.cols:
            raise errors.BadDataError(self.cols, len(data[0]))

        # Ordinarily, we are using record arrays, but for numpy savetxt we want a 2-D array
        record_data = util.from_record_array(data)
        # append data to in-memory data
        if self.data.size > 0:
            self.data = np.vstack((self.data, record_data))
        else:
            self.data = record_data

        # append data to file
        self._save_data(data)

    def get_data(self, limit, start, transpose, simple_only):
        if transpose:
            raise RuntimeError("Transpose specified for simple data format: not supported")

        if limit is None:
            data = self.data[start:]
        else:
            data = self.data[start:start + limit]
        # nrows should be zero for an empty row
        nrows = len(data) if data.size > 0 else 0
        return data, start + nrows

    def has_more(self, pos):
        # cheesy hack: if pos == 0, we only need to check whether
        # the filesize is nonzero
        if pos == 0:
            return os.path.getsize(self.filename) > 0
        else:
            nrows = len(self.data) if self.data.size > 0 else 0
            return pos < nrows


# HDF DATA FILES
class HDF5MetaData(object):
    """
    Class to store metadata inside the file itself.

    Like IniData, use this by subclassing.  I anticipate simply moving
    this code into the HDF5Dataset class once it is working, since we
    don't plan to support accessing HDF5 datasets with INI files once
    this version works.
    """

    comment_type = [
        ('Timestamp', np.float64),
        ('User', h5py.special_dtype(vlen=str)),
        ('Comment', h5py.special_dtype(vlen=str))
    ]

    def load(self):
        """
        Load and save do nothing because HDF5 metadata is accessed live.
        """
        pass

    def save(self):
        """
        Load and save do nothing because HDF5 metadata is accessed live.
        """
        pass

    @property
    def dtype(self):
        return self.dataset.dtype

    def initialize_info(self, title, indep, dep):
        """
        Initializes the metadata for a newly created dataset.
        """
        t = time()

        attrs = self.dataset.attrs
        attrs['Title'] = title
        attrs['Access Time'] = t
        attrs['Modification Time'] = t
        attrs['Creation Time'] = t
        attrs['Comments'] = np.ndarray((0,), dtype=self.comment_type)

        for idx, i in enumerate(indep):
            prefix = 'Independent{}.'.format(idx)
            attrs[prefix + 'label'] = i.label
            attrs[prefix + 'shape'] = i.shape
            attrs[prefix + 'datatype'] = i.datatype
            attrs[prefix + 'unit'] = i.unit

        for idx, d, in enumerate(dep):
            prefix = 'Dependent{}.'.format(idx)
            attrs[prefix + 'label'] = d.label
            attrs[prefix + 'legend'] = d.legend
            attrs[prefix + 'shape'] = d.shape
            attrs[prefix + 'datatype'] = d.datatype
            attrs[prefix + 'unit'] = d.unit

    def access(self):
        self.dataset.attrs['Access Time'] = time()

    def get_independents(self):
        attrs = self.dataset.attrs
        rv = []
        for idx in range(maxsize):
            prefix = 'Independent{}.'.format(idx)
            key = prefix + 'label'
            if key in attrs:
                label = attrs[prefix + 'label']
                shape = attrs[prefix + 'shape']
                datatype = attrs[prefix + 'datatype']
                unit = attrs[prefix + 'unit']
                rv.append(Independent(label, shape, datatype, unit))
            else:
                return rv

    def get_dependents(self):
        attrs = self.dataset.attrs
        rv = []
        for idx in range(maxsize):
            prefix = 'Dependent{}.'.format(idx)
            key = prefix + 'label'
            if key in attrs:
                label = attrs[prefix + 'label']
                legend = attrs[prefix + 'legend']
                shape = attrs[prefix + 'shape']
                datatype = attrs[prefix + 'datatype']
                unit = attrs[prefix + 'unit']
                rv.append(Dependent(label, legend, shape, datatype, unit))
            else:
                return rv

    def get_row_type(self):
        column_types = []
        for col in self.get_independents() + self.get_dependents():
            base_type = col.datatype
            if base_type in ['v', 'c']:
                unit_tag = '[{}]'.format(col.unit)
            else:
                unit_tag = ''
            if len(col.shape) > 1:
                shape_tag = '*{}'.format(len(col.shape))
                comment = util.braced(','.join(str(s) for s in col.shape))
            elif col.shape[0] > 1:
                shape_tag = '*'
                comment = util.braced(str(col.shape[0]))
            else:
                shape_tag = ''
                comment = ''
            column_types.append(shape_tag + base_type + unit_tag + comment)
        type_tag = '*({})'.format(','.join(column_types))
        return type_tag

    def get_transpose_type(self):
        column_type = []
        for col in self.get_independents() + self.get_dependents():
            base_type = col.datatype
            if base_type in ['v', 'c']:
                unit_tag = '[{}]'.format(col.unit)
            else:
                unit_tag = ''
            if len(col.shape) > 1:
                shape_tag = '*{}'.format(len(col.shape) + 1)
                comment = util.braced('N,' + ','.join(str(s) for s in col.shape))
            elif col.shape[0] > 1:
                shape_tag = '*2'
                comment = util.braced('N,' + str(col.shape[0]))
            else:
                shape_tag = '*'
                comment = ''
            column_type.append(shape_tag + base_type + unit_tag + comment)
        type_tag = '({})'.format(','.join(column_type))
        return type_tag

    def add_param(self, name, data):
        keyname = 'Param.{}'.format(name)
        if keyname in self.dataset.attrs:
            raise errors.ParameterInUseError(name)
        value = labrad_urlencode(data)
        self.dataset.attrs[keyname] = value

    def get_parameter(self, name, case_sensitive=True):
        """
        Get a parameter from the dataset.
        """
        keyname = 'Param.{}'.format(name)
        if case_sensitive:
            if keyname in self.dataset.attrs:
                return labrad_urldecode(self.dataset.attrs[keyname])
        else:
            for k in self.dataset.attrs:
                if k.lower() == keyname.lower():
                    return labrad_urldecode(self.dataset.attrs[k])
        raise errors.BadParameterError(name)

    def get_param_names(self):
        """
        Get the names of all dataset parameters.

        Parameter names in the HDF5 file are prefixed with 'Param.' to avoid
        conflicts with the other metadata.
        """
        return [str(k[6:]) for k in self.dataset.attrs if k.startswith('Param.')]

    def add_comment(self, user, comment):
        """
        Add a comment to the dataset.
        """
        t = time()
        new_comment = np.array([(t, user, comment)], dtype=self.comment_type)
        old_comments = self.dataset.attrs['Comments']
        data = np.hstack((old_comments, new_comment))
        self.dataset.attrs.create('Comments', data, dtype=self.comment_type)

    def get_comments(self, limit, start):
        """
        Get comments in [(datetime, username, comment), ...] format.
        """
        if limit is None:
            raw_comments = self.dataset.attrs['Comments'][start:]
        else:
            raw_comments = self.dataset.attrs['Comments'][start:start + limit]
        comments = [(datetime.datetime.fromtimestamp(c[0]), str(c[1]), str(c[2])) for c in raw_comments]
        return comments, start + len(comments)

    def num_comments(self):
        return len(self.dataset.attrs['Comments'])


class ExtendedHDF5Data(HDF5MetaData):
    """
    Dataset backed by HDF5 file.

    This supports the extended dataset format which allows each column
    to have a different type and to be arrays themselves.
    """

    def __init__(self, fh):
        self._file = fh
        if 'Version' not in self.file.attrs:
            self.file.attrs['Version'] = np.asarray([3, 0, 0], dtype=np.int32)
        self.version = np.asarray(self.file.attrs['Version'], np.int32)

    def initialize_info(self, title, indep, dep):
        """
        Initialize the columns when creating a new dataset.
        """
        dtype = []
        for idx, col in enumerate(indep + dep):
            shape = col.shape
            ttag = col.datatype
            unit = col.unit
            if len(shape) == 1 and shape[0] == 1:
                shapestr = ''
            else:
                shapestr = str(tuple(shape))
            varname = 'f{}'.format(idx)
            if unit != '' and ttag not in ['v', 'c']:
                raise RuntimeError('Unit {} specfied for datatype {}.  Only v and c may have units'.format(unit, ttag))
            if ttag == 'i':
                dtype.append((varname, shapestr + 'i4'))
            elif ttag == 's':
                if shapestr:
                    raise ValueError("Cannot create string array column")
                dtype.append((varname, h5py.special_dtype(vlen=str)))
            elif ttag == 't':
                dtype.append((varname, shapestr + 'i8'))
            elif ttag == 'v':
                dtype.append((varname, shapestr + 'f8'))
            elif ttag == 'c':
                dtype.append((varname, shapestr + 'c16'))
            else:
                raise RuntimeError("Invalid type tag {}".format(ttag))

        self.file.create_dataset('DataVault', (0,), dtype=dtype, maxshape=(None,))
        HDF5MetaData.initialize_info(self, title, indep, dep)

    @property
    def file(self):
        return self._file()

    @property
    def dataset(self):
        return self.file["DataVault"]

    def add_data(self, data):
        """
        Adds one or more rows or data from a numpy struct array.
        """
        new_rows = len(data)
        old_rows = self.dataset.shape[0]
        self.dataset.resize((old_rows + new_rows,))
        self.dataset[old_rows:(old_rows + new_rows)] = data

    def get_data(self, limit, start, transpose, simple_only):
        """
        Get up to limit rows from a dataset.
        """
        if simple_only:
            datatype = self.dataset.dtype
            for idx in range(len(datatype)):
                if datatype[idx] != np.float64:
                    raise errors.DataVersionMismatchError()
        if transpose:
            return self.get_data_transpose(limit, start)

        data, new_pos = self._get_data(limit, start)
        row_data = [tuple(row) for row in data]
        return row_data, new_pos

    def get_data_transpose(self, limit, start):
        struct_data, new_pos = self._get_data(limit, start)
        columns = []
        for idx in range(len(struct_data.dtype)):
            col = struct_data['f{}'.format(idx)]
            # Strings are stored as hdf5 vlen objects.  Numpy can't do
            # variable length strings, so they get encoded as object
            # arrays by hdf5.  we don't know how to flatten object
            # arrays so we special case vlen types here and convert
            # them to lists.  Also, h5py has a bug where when you
            # index a dataset with a compound type, it loses the
            # special dtype information, so we pull it directly from
            # self.dataset.dtype rather than the data returned by
            # _getData
            if self.dataset.dtype[idx] == np.object:
                base_type = h5py.check_dtype(vlen=self.dataset.dtype[idx])
                if not base_type or not issubclass(base_type, str):
                    raise RuntimeError(
                        "Found object type array, but not vlen str.  Not supported.  This shouldn't happen")
                col = [base_type(x) for x in col]
            columns.append(col)
        columns = tuple(columns)
        return columns, new_pos

    def _get_data(self, limit, start):
        if limit is None:
            struct_data = self.dataset[start:]
        else:
            struct_data = self.dataset[start:start + limit]
        return struct_data, start + struct_data.shape[0]

    def __len__(self):
        return self.dataset.shape[0]

    def has_more(self, pos):
        return pos < len(self)

    def shape(self):
        cols = len(self.get_independents() + self.get_dependents())
        rows = self.dataset.shape[0]
        return rows, cols


class SimpleHDF5Data(HDF5MetaData):
    """
    Basic dataset backed by HDF5 file.

    This is a very simple implementation that only supports a single 2-D dataset
    of all floats.  HDF5 files support multiple types, multiple dimensions, and
    a filesystem-like tree of datasets within one file. Here, the single dataset
    is stored in /DataVault within the HDF5 file.
    """
    def __init__(self, fh):
        self._file = fh
        if 'Version' not in self.file.attrs:
            self.file.attrs['Version'] = np.asarray([2, 0, 0], dtype=np.int32)
        self.version = np.asarray(self.file.attrs['Version'], dtype=np.int32)

    def initialize_info(self, title, indep, dep):
        ncol = len(indep) + len(dep)
        dtype = [('f{}'.format(idx), np.float64) for idx in range(ncol)]
        if 'DataVault' not in self.file:
            self.file.create_dataset('DataVault', (0,), dtype=dtype, maxshape=(None,))
        HDF5MetaData.initialize_info(self, title, indep, dep)

    @property
    def file(self):
        return self._file()

    @property
    def dataset(self):
        return self.file["DataVault"]

    def add_data(self, data):
        """
        Adds one or more rows or data from a 2D array of floats.
        """
        new_rows = data.shape[0]
        old_rows = self.dataset.shape[0]
        # if data.shape[1] != len(self.dataset.dtype):
        #    raise errors.BadDataError(len(self.dataset.dtype), data.shape[1])

        self.dataset.resize((old_rows + new_rows,))
        # new_data = np.zeros((new_rows,), dtype=self.dataset.dtype)
        # for col in range(data.shape[1]):
        #    field = "f%d" % (col,)
        #    new_data[field] = data[:,col]
        self.dataset[old_rows:(old_rows + new_rows)] = data

    def get_data(self, limit, start, transpose, simple_only):
        """
        Get up to <limit> rows from a dataset.
        """
        if transpose:
            raise RuntimeError("Transpose specified for simple data format: not supported")
        if limit is None:
            struct_data = self.dataset[start:]
        else:
            struct_data = self.dataset[start:start + limit]
        columns = []
        for idx in range(len(struct_data.dtype)):
            columns.append(struct_data['f{}'.format(idx)])
        data = np.column_stack(columns)
        return data, start + data.shape[0]

    def __len__(self):
        return self.dataset.shape[0]

    def has_more(self, pos):
        return pos < len(self)

    def shape(self):
        # todo: maybe better way of doing this? isn't cols just self.dataset.shape[1]?
        cols = len(self.get_independents() + self.get_dependents())
        rows = self.dataset.shape[0]
        return rows, cols


class ARTIQHDF5Data(HDF5MetaData):
    """
    An ARTIQ dataset backed by a HDF5 file.

    This is a very barebones implementation that assumes the first column
    of data is the independent variable, and all subsequent columns are the
    dependent variables.
    Independent and dependent variables have been given generic names since
    these aren't typically specified in ARTIQs dataset management system.
    Here, the dataset(s) are stored in /datasets within the HDF5 file.
    For simplicity, we assume that there is only one dataset.
    """
    def __init__(self, fh):
        self._file = fh
        # get datasets
        dataset_group = self.file["datasets"]
        assert isinstance(dataset_group, h5py.Group)
        # todo: figure a better way of accommodating multiple datasets
        assert len(dataset_group) == 1
        self.dataset_name = list(self.file["datasets"].keys())[0]

        # set versioning
        if 'Version' not in self.file.attrs:
            self.file.attrs['Version'] = np.asarray([2, 1, 0], dtype=np.int32)
        self.version = np.asarray(self.file.attrs['Version'], dtype=np.int32)

        # create comments
        if 'Comments' not in self.file.attrs:
            self.dataset.attrs['Comments'] = list()

    @property
    def file(self):
        return self._file()

    @property
    def dataset(self):
        return self.file["datasets"][self.dataset_name]

    def __len__(self):
        return self.dataset.shape[0]

    def initialize_info(self, title, indep, dep):
        raise NotImplementedError

    def add_data(self, data):
        raise NotImplementedError

    def get_independents(self):
        """
        todo: justify
        """
        prefix = 'Independent{}.'.format(1)
        label = prefix + 'label'
        shape = 1
        datatype = 'v'
        unit = 'arb.'
        return [Independent(label, shape, datatype, unit)]

    def get_dependents(self):
        rv = []
        num_dependents = self.dataset.shape[1] - 1
        for idx in range(num_dependents):
            prefix = 'Dependent{}.'.format(idx)
            label = prefix + 'label'
            legend = prefix + 'legend'
            shape = 1
            datatype = 'v'
            unit = 'arb.'
            rv.append(Dependent(label, legend, shape, datatype, unit))
        return rv

    def get_data(self, limit, start, transpose, simple_only):
        """
        Get up to <limit> rows from a dataset.
        """
        if transpose:
            raise RuntimeError("Transpose specified for simple data format: not supported")
        struct_data = self.dataset[start:] if limit is None else self.dataset[start:start + limit]
        columns = []
        for idx in range(len(self.get_independents() + self.get_dependents())):
            columns.append(struct_data[:, idx])
        data = np.column_stack(columns)
        return data, start + data.shape[0]

    def has_more(self, pos):
        return pos < len(self)

    def shape(self):
        cols = len(self.get_independents() + self.get_dependents())
        rows = self.dataset.shape[0]
        return rows, cols


class MultipleHDF5Data(HDF5MetaData):
    """
    An HDF5Data object used to represent a single dataset
        when an ARTIQ hdf5 file has multiple datasets.
    """
    def __init__(self, fh, dataset_name):
        self._file = fh
        self.dataset_name = dataset_name

        # get specific dataset
        dataset_group = self.file["datasets"][dataset_name]

        # set versioning (can't assign to file since we're read-only)
        self.version = np.asarray([2, 1, 0], dtype=np.int32)

    @property
    def file(self):
        return self._file()

    @property
    def dataset(self):
        return self.file["datasets"][self.dataset_name]

    def __len__(self):
        return self.dataset.shape[0]

    def initialize_info(self, title, indep, dep):
        raise NotImplementedError

    def add_data(self, data):
        raise NotImplementedError

    def access(self):
        # todo: raise error?
        pass

    def add_param(self, name, data):
        # todo: raise error?
        pass

    def add_comment(self, user, comment):
        # todo: raise error?
        pass

    def num_comments(self):
        return 0

    def get_independents(self):
        """
        todo: justify
        """
        prefix = 'Independent{}.'.format(1)
        label = prefix + 'label'
        shape = 1
        datatype = 'v'
        unit = 'arb.'
        return [Independent(label, shape, datatype, unit)]

    def get_dependents(self):
        rv = []
        num_dependents = self.dataset.shape[1] - 1
        for idx in range(num_dependents):
            prefix = 'Dependent{}.'.format(idx)
            label = prefix + 'label'
            legend = prefix + 'legend'
            shape = 1
            datatype = 'v'
            unit = 'arb.'
            rv.append(Dependent(label, legend, shape, datatype, unit))
        return rv

    def get_data(self, limit, start, transpose, simple_only):
        """
        Get up to <limit> rows from a dataset.
        """
        if transpose:
            raise RuntimeError("Transpose specified for simple data format: not supported")
        struct_data = self.dataset[start:] if limit is None else self.dataset[start:start + limit]
        columns = []
        for idx in range(len(self.get_independents() + self.get_dependents())):
            columns.append(struct_data[:, idx])
        data = np.column_stack(columns)
        return data, start + data.shape[0]

    def has_more(self, pos):
        return pos < len(self)

    def shape(self):
        cols = len(self.get_independents() + self.get_dependents())
        rows = self.dataset.shape[0]
        return rows, cols


# FILE BACKEND CREATION
def open_hdf5_file(filename, dataset_name=None):
    """
    Factory for HDF5 files.

    We check the version of the file to construct the proper class.  Currently, only two
    options exist: version 2.0.0 -> legacy format, 3.0.0 -> extended format.
    Version 1 is reserved for CSV files.
    """
    # selection of a specific dataset name means we have multiple datasets in the file
    # and we have to use MultipleHDF5Data
    if dataset_name is not None:
        fh = SelfClosingFile(h5py.File, open_args=(filename, 'r'))
        return MultipleHDF5Data(fh, dataset_name)

    # instantiate the file
    fh = SelfClosingFile(h5py.File, open_args=(filename, 'a'))

    # accommodate artiq files
    if 'artiq_version' in fh().keys():
        return ARTIQHDF5Data(fh)

    # instantiate correct data object using versioning
    try:
        version = fh().attrs['Version']
        if (version[0] == 2) and (version[1] == 0):
            return SimpleHDF5Data(fh)
        elif version[0] == 3:
            return ExtendedHDF5Data(fh)
    except Exception as e:
        print('Error:', e)


def create_backend(filename, title, indep, dep, extended):
    """
    Create a data object for a new dataset.
    """
    hdf5_file = filename + '.hdf5'
    fh = SelfClosingFile(h5py.File, open_args=(hdf5_file, 'a'))
    data = ExtendedHDF5Data(fh) if extended else SimpleHDF5Data(fh)
    data.initialize_info(title, indep, dep)
    return data


def open_backend(filename, dataset_name=None):
    """
    Make a data object that manages in-memory and on-disk storage for a dataset.

    filename should be specified without a file extension. If there is an existing
    file in csv format, we create a backend of the appropriate type. If
    no file exists, we create a new backend to store data in binary form.
    """
    csv_file = filename + '.csv'
    hdf5_file = filename + '.hdf5'
    h5_file = filename + '.h5'

    # check to see whether the CSV file exists
    if os.path.exists(csv_file):
        return CsvNumpyData(csv_file)
    # check to see whether the HDF5 file exists
    elif os.path.exists(hdf5_file):
        return open_hdf5_file(hdf5_file, dataset_name)
    elif os.path.exists(h5_file):
        return open_hdf5_file(h5_file, dataset_name)
    # return an error if the file doesn't exist
    # (though this shouldn't happen since we check several times)
    else:
        raise errors.DatasetNotFoundError(filename)
