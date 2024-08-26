from __future__ import absolute_import

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks
from labrad.server import LabradServer, Signal, setting

try:
    import win32api
except ImportError:
    win32api = False
    print("Win32 API missing. If you're running on windows, this is a problem")
import numpy as np
from . import errors
from os import remove

# todo: implement ability to delete things
# todo: fix documentation
# todo: fix up function names
# todo: make simple if statements oneliners


class DataVault(LabradServer):
    """
    Stores and manages data/datasets using the HDF5 format.
    """

    name = "Data Vault"

    # SETUP

    def __init__(self, session_store):
        LabradServer.__init__(self)
        self.session_store = session_store

        # session signals
        self.onNewDir = Signal(543617, "signal: new dir", "s")
        self.onNewDataset = Signal(543618, "signal: new dataset", "s")
        self.onTagsUpdated = Signal(543622, "signal: tags updated", "*(s*s)*(s*s)")
        # dataset signals
        self.onDataAvailable = Signal(543619, "signal: data available", "")
        self.onNewParameter = Signal(543620, "signal: new parameter", "")
        self.onCommentsAvailable = Signal(543621, "signal: comments available", "")

    def initServer(self):
        # create root session
        _root = self.session_store.get([""])
        # close all datasets on program shutdown
        if win32api:
            win32api.SetConsoleCtrlHandler(self._close_all_datasets, True)
        # create LoopingCall to save routinely save datasets in background
        # todo: make save interval customizable
        self.saveDatasetTimer = LoopingCall(self._save_all_datasets)
        self.saveDatasetTimer.start(300)

    def _save_all_datasets(self):
        """
        Save all datasets routinely.
        Prevents data from being corrupted due to unforeseen/uninterruptible events.
        """
        # get all datasets across all sessions
        all_sessions = list(self.session_store.get_all())
        all_datasets = [session.datasets.values() for session in all_sessions]
        # flatten list of datasets
        all_containers = set(
            [
                dataset.data
                for session_datasets in all_datasets
                for dataset in session_datasets
            ]
        )

        # flush (i.e. save) all file data
        for container in all_containers:
            try:
                # container is Data object (e.g. SimpleHDF5Data)
                # container._file is SelfClosingFile
                # container._file._file is actual data file object
                if hasattr(container._file, "_file"):
                    container._file._file.flush()
            except Exception as e:
                print(e)

    def _close_all_datasets(self, signal):
        """
        Close all open datasets when we shut down.
        Needed on shutdown and disconnect since open HDF5 files may become corrupted.
        """
        # get all datasets across all sessions
        all_sessions = list(self.session_store.get_all())
        all_datasets = [session.datasets.values() for session in all_sessions]
        # flatten list of datasets
        all_containers = set(
            [
                dataset.data
                for session_datasets in all_datasets
                for dataset in session_datasets
            ]
        )

        # close all the files
        for container in all_containers:
            datafile = container._file
            # cancel the timeout poll loop if it exists
            if hasattr(datafile, "_fileTimeoutCall"):
                datafile._fileTimeoutCall.cancel()
            # close the file
            try:
                datafile._file_timeout()
            except Exception as e:
                print(e)

    # CONTEXT MANAGEMENT

    def context_key(self, c):
        """
        The key used to identify a given context for notifications.
        """
        return c.ID

    def initContext(self, c):
        # start in the root session
        c["path"] = [""]
        # start listening to the root session
        c["session"] = self.session_store.get([""])
        c["session"].listeners.add(self.context_key(c))

    def expireContext(self, c):
        """
        Stop sending any signals to this context.
        """
        key = self.context_key(c)

        def removeFromList(ls):
            if key in ls:
                ls.remove(key)

        for session in self.session_store.get_all():
            removeFromList(session.listeners)
            for dataset in session.datasets.values():
                removeFromList(dataset.listeners)
                removeFromList(dataset.param_listeners)
                removeFromList(dataset.comment_listeners)

    # GETTING CONTEXT OBJECTS

    def get_session(self, c):
        """
        Get a session object for the current path.
        """
        return c["session"]

    def get_dataset(self, c):
        """
        Get a dataset object for the current dataset.
        """
        if "dataset" not in c:
            raise errors.NoDatasetError()
        return c["datasetObj"]

    # GENERAL

    @setting(5, returns=["*s"])
    def dump_existing_sessions(self, c):
        return ["/".join(session.path) for session in self.session_store.get_all()]

    # DIRECTORY NAVIGATION

    @setting(
        6,
        tag_filters=["s", "*s"],
        include_tags="b",
        returns=["*s{subdirs}, *s{datasets}", "*(s*s){subdirs}, *(s*s){datasets}"],
    )
    def dir(self, c, tag_filters="-trash", include_tags=False):
        """
        Get subdirectories and datasets in the current directory.
        """
        # ensure tagFilters is a list object
        tag_filters = [tag_filters] if isinstance(tag_filters, str) else tag_filters

        # get contents of session
        sess = self.get_session(c)
        dirs, datasets = sess.list_contents(tag_filters)

        # parse tags
        if include_tags:
            dirs, datasets = sess.get_tags(dirs, datasets)
        return dirs, datasets

    @setting(
        7,
        path=[
            "{get current directory}",
            "s{change into this directory}",
            "*s{change into each directory in sequence}",
            "w{go up by this many directories}",
        ],
        create="b",
        returns="*s",
    )
    def cd(self, c, path=None, create=False):
        """
        Change the current directory.

        The empty string '' refers to the root directory. If the 'create' flag
        is set to true, new directories will be created as needed.
        Returns the path to the new current directory.
        """
        # empty call returns current path
        if path is None:
            return c["path"]

        # copy the current path
        temp = c["path"][:]

        # go up directories if path is word/int
        if isinstance(path, (int, int)):
            if path > 0:
                temp = temp[:-path]
                if not len(temp):
                    temp = [""]

        # go down directories if path is str
        else:
            if isinstance(path, str):
                path = [path]
            # go down each subdirectory specified
            for segment in path:
                # empty calls in the directory list moves us back to the root directory
                if segment == "":
                    temp = ["", "data"]
                else:
                    temp.append(segment)
                # check that subdirectory will exist
                if (not self.session_store.exists(temp)) and (not create):
                    raise errors.DirectoryNotFoundError(temp)
                # touch the session
                _session = self.session_store.get(temp)

        # change sessions
        if c["path"] != temp:
            # remove context as listener to old session
            key = self.context_key(c)
            c["session"].listeners.remove(key)
            # add context as listener to new session
            session = self.session_store.get(temp)
            session.listeners.add(key)
            # store new values
            c["session"] = session
            c["path"] = temp

        return c["path"]

    # CREATING DATASETS/DIRECTORIES

    @setting(8, name="s", returns="*s")
    def mkdir(self, c, name):
        """
        Make a new subdirectory in the current directory.

        The current directory remains selected.
        You must use the 'cd' command to select the newly-created directory.
        Directory name cannot be empty.
        Returns the path to the created directory.
        """
        if name == "":
            raise errors.EmptyNameError()
        path = c["path"] + [name]

        if self.session_store.exists(path):
            raise errors.DirectoryExistsError(path)
        # create a new directory
        _sess = self.session_store.get(path)
        return path

    @setting(
        9,
        name="s",
        independents=["*s", "*(ss)"],
        dependents=["*s", "*(sss)"],
        returns="(*s{path}, s{name})",
    )
    def new(self, c, name, independents, dependents):
        """
        Create a new Dataset.

        Independent and dependent variables can be specified either
        as clusters of strings, or as single strings.  Independent
        variables have the form (label, units) or 'label [units]'.
        Dependent variables have the form (label, legend, units)
        or 'label (legend) [units]'.  Label is meant to be an
        axis label that can be shared among traces, while legend is
        a legend entry that should be unique for each trace.
        Returns the path and name for this dataset.
        """
        # ensure valid filename
        if "." in name:
            raise Exception("Error: invalid title (contains periods).")

        session = self.get_session(c)
        dataset = session.new_dataset(name or "untitled", independents, dependents)
        c["dataset"] = dataset.name  # not the same as name; has number prefixed
        c["datasetObj"] = dataset
        c["filepos"] = 0  # start at the beginning
        c["commentpos"] = 0
        c["writing"] = True
        return c["path"], c["dataset"]

    @setting(
        1009, name="s", independents="*(s*iss)", dependents="*(ss*iss)", returns=["*ss"]
    )
    def new_ex(self, c, name, independents, dependents):
        """
        Create a new extended dataset.

        Independents are specified as: (label, shape, type, unit)
        Dependents are specified as: (label, legend, shape, type, unit)

        Label and legend have the same meaining as in regular new()
        shape is a list of integers representing the shape of the array.
            For A scalar column, use [1].
        type is the column data type including a type tag if applicable.
            Types use the labrad typetags, but only scalar types are supported.
            i:          32 bit integer
            v:          double precision floating point with unit.  Use v[] for scalar
            c:          double precision complex with unit.  Use c[] for scalar
            s:          string.  The string must be plain ASCII or UTF-8 encoded
                        unicode (until labrad has native unicode support)
                        Arbitrary binary data is *not* supported.
            t:          Timestamp
        unit is the unit of the column.  Only applies for types 'v' and 'c'.
            It *must* be an empty string ('') for i,s,t datatypes

        Note that any dataset created with this function that does not conform
        to the old style restrictions will show up as an empty dataset to legacy
        code.  The name and parameters will be there, but no actual data.

        The legacy format requires each column be a scalar v[unit] type.
        """
        # ensure valid filename
        if "." in name:
            raise Exception("Error: invalid title (contains periods).")

        session = self.get_session(c)
        dataset = session.new_dataset(name, independents, dependents, extended=True)
        c["dataset"] = dataset.name  # not the same as name; has number prefixed
        c["datasetObj"] = dataset
        c["filepos"] = 0  # start at the beginning
        c["commentpos"] = 0
        c["writing"] = True
        return c["path"], c["dataset"]

    @setting(10, name=["s", "w"], append="b", returns="(*s{path}, s{name})")
    def open(self, c, name, append=False):
        """
        Open a Dataset for reading.

        You can specify the dataset by name or number.
        Returns the path and name for this dataset.
        """
        session = self.get_session(c)
        dataset = session.open_dataset(name)
        c["dataset"] = dataset.name  # not the same as name; has number prefixed
        c["datasetObj"] = dataset
        c["filepos"] = 0
        c["commentpos"] = 0
        c["writing"] = append
        key = self.context_key(c)
        dataset.keep_streaming(key, 0)
        dataset.keep_streaming_comments(key, 0)
        return c["path"], c["dataset"]

    @setting(11, name=["s", "w"], returns="b")
    def delete(self, c, name):
        """
        # todo: make inclusive of folders as well as datasets
        Delete a Dataset.

        You can specify the dataset by name or number.
        Returns the success status of the dataset deletion operation
        """
        # todo: check if dataset exists
        # todo: check if dataset is currently being used
        # todo: delete file
        # todo: modify session/sessionstore
        session = self.get_session(c)
        dataset = session.open_dataset(name)

        # todo tmp remove
        # get all datasets across all sessions
        all_sessions = list(self.session_store.get_all())
        all_datasets = [session.datasets.values() for session in all_sessions]
        # flatten list of datasets
        all_containers = set(
            [
                dataset.data
                for session_datasets in all_datasets
                for dataset in session_datasets
            ]
        )

        # flush (i.e. save) all file data
        for container in all_containers:
            try:
                # container is Data object (e.g. SimpleHDF5Data)
                # container._file is SelfClosingFile
                # container._file._file is actual data file object
                if hasattr(container._file, "_file"):
                    container._file._file.flush()
            except Exception as e:
                print(e)
        return False

    # GET DATA

    @setting(1010, returns="s")
    def get_version(self, c):
        """
        Get version of current dataset.
            1.x:   CSV dataset
            2.x:   Simple HDF5 dataset
            3.x:   Extended dataset
        Returns:
            (str)   :   dataset version.
        """
        dataset = self.get_dataset(c)
        return dataset.version()

    @setting(
        20,
        data=["*v: add one row of data", "*2v: add multiple rows of data"],
        returns="",
    )
    def add(self, c, data):
        """
        Add data to the current dataset.

        The number of elements in each row of data must be equal
        to the total number of variables in the data set
        (independents + dependents).
        """
        dataset = self.get_dataset(c)
        if not c["writing"]:
            raise errors.ReadOnlyError()
        data = np.atleast_2d(np.asarray(data))
        # fromarrays is faster than fromrecords, and when we have a simple 2-D array
        # we can just transpose the array.
        rec_data = np.core.records.fromarrays(data.T, dtype=dataset.data.dtype)
        dataset.add_data(rec_data)

    @setting(1020, data="?", returns="")
    def add_ex(self, c, data):
        """
        Add data to the current dataset in the extended format.

        Data should be a list of clusters suitable for the current
        dataset.  For instance, for a dataset with a timestamp, an
        integer, and a voltage the data type should be *(tiv[V]).

        Because pylabrad is inefficient at packing and unpacking lists
        of clusters, consider using add_ex_t for performance.
        """
        dataset = self.get_dataset(c)
        if not c["writing"]:
            raise errors.ReadOnlyError()
        list_data = [tuple(row) for row in data]
        dataset.add_data(
            np.core.records.fromrecords(list_data, dtype=dataset.data.dtype)
        )

    @setting(2020, data="?", returns="")
    def add_ex_t(self, c, data):
        """
        Add data to the current dataset in the extended format.

        Data should be a cluster of List/array types, one per column.
        This is a transposed version of add_ex, and will have better
        performance.
        """
        dataset = self.get_dataset(c)
        if not c["writing"]:
            raise errors.ReadOnlyError()
        dataset.add_data(np.core.records.fromarrays(data, dtype=dataset.data.dtype))

    @setting(21, limit="w", start_over="b", returns="*2v")
    def get(self, c, limit=None, start_over=False):
        """
        Get data from the current dataset.

        Limit is the maximum number of rows of data to return, with
        the default being to return the whole dataset.  Setting the
        startOver flag to true will return data starting at the beginning
        of the dataset.  By default, only new data that has not been seen
        in this context is returned.
        """
        dataset = self.get_dataset(c)
        c["filepos"] = 0 if start_over else c["filepos"]
        data, c["filepos"] = dataset.get_data(limit, c["filepos"], simple_only=True)
        key = self.context_key(c)
        dataset.keep_streaming(key, c["filepos"])
        return data

    @setting(1021, limit="w", start_over="b", returns="?")
    def get_ex(self, c, limit=None, start_over=False):
        """
        Get data from the current dataset in the extended format.

        Data is returned as *(...).  That is, a list of clusters, one per
        row.  Because of the inefficiency of python flattening and
        unflattening cluster arrays, consider using get_ex_t for
        performance.
        """
        dataset = self.get_dataset(c)
        c["filepos"] = 0 if start_over else c["filepos"]
        data, c["filepos"] = dataset.get_data(limit, c["filepos"], transpose=False)
        ctx = self.context_key(c)
        dataset.keep_streaming(ctx, c["filepos"])
        return data

    @setting(2021, limit="w", start_over="b", returns="?")
    def get_ex_t(self, c, limit=None, start_over=False):
        """
        Get data from the current dataset in the extended format.

        Data is returned as (*c1*c2*c3): that is, a cluster of lists,
        one per row.  Each column list is N+1 dimensional, where N is
        the array dimension of that particular column.  Scalar columns
        result in 1-D lists.  This is the transpose of the normal
        format, but is more efficient for pylabrad flatten/unflatten
        code.
        """
        dataset = self.get_dataset(c)
        c["filepos"] = 0 if start_over else c["filepos"]
        data, c["filepos"] = dataset.get_data(limit, c["filepos"], transpose=True)
        ctx = self.context_key(c)
        dataset.keep_streaming(ctx, c["filepos"])
        return data

    # VARIABLES

    @setting(100, returns="(*(ss){independents}, *(sss){dependents})")
    def variables(self, c):
        """
        Get the independent and dependent variables for the current dataset.

        Each independent variable is a cluster of (label, units).
        Each dependent variable is a cluster of (label, legend, units).
        Label is meant to be an axis label, which may be shared among several
        traces, while legend is unique to each trace.
        """
        ds = self.get_dataset(c)
        ind = [(i.label, i.unit) for i in ds.get_independents()]
        dep = [(d.label, d.legend, d.unit) for d in ds.get_dependents()]
        return ind, dep

    @setting(101, returns="*(s*iss), *(ss*iss)")
    def variables_ex(self, c):
        """
        Get the independent and dependent variables for the current dataset in the extended format

        Returns (*indep, *dep)

        The independent variables are a cluster of (label, shape, type, unit)
        The dependent variables are a cluster of (label, legend, shape, type, unit)

        See new_ex for descriptions of these items.
        """
        ds = self.get_dataset(c)
        ind = ds.get_independents()
        dep = ds.get_dependents()
        return ind, dep

    @setting(102, returns="s")
    def row_type(self, c):
        """
        Returns the labrad typetag for a single row of the current dataset.
        This is mostly only useful with the extended format.
        """
        ds = self.get_dataset(c)
        return ds.get_row_type()

    @setting(103, returns="s")
    def transpose_type(self, c):
        """
        Returns the labrad typetag for accessing the dataset with the transpose commands
        add_ex_t and get_ex_t.
        """
        ds = self.get_dataset(c)
        return ds.get_transpose_type()

    @setting(104, returns="(i, i)")
    def shape(self, c):
        """
        Returns the shape of the dataset.
        """
        ds = self.get_dataset(c)
        return ds.shape()

    # METADATA

    @setting(120, "Parameters", returns="*s")
    def parameters(self, c):
        """
        Get a list of parameter names.
        """
        dataset = self.get_dataset(c)
        key = self.context_key(c)
        dataset.param_listeners.add(key)  # send a message when new parameters are added
        return dataset.get_param_names()

    @setting(121, name="s", returns="")
    def add_parameter(self, c, name, data):
        """
        Add a new parameter to the current dataset.
        """
        dataset = self.get_dataset(c)
        dataset.add_parameter(name, data)

    @setting(124, "add parameters", params="?{((s?)(s?)...)}", returns="")
    def add_parameters(self, c, params):
        """
        Add a new parameter to the current dataset.
        """
        dataset = self.get_dataset(c)
        dataset.add_parameters(params)

    @setting(126, "get name", returns="s")
    def get_name(self, c):
        """
        Get the name of the current dataset.
        """
        dataset = self.get_dataset(c)
        name = dataset.name
        return name

    @setting(122, "get parameter", name="s")
    def get_parameter(self, c, name, case_sensitive=True):
        """
        Get the value of a parameter.
        """
        dataset = self.get_dataset(c)
        return dataset.get_parameter(name, case_sensitive)

    @setting(123, "get parameters")
    def get_parameters(self, c):
        """
        Get all parameters.

        Returns a cluster of (name, value) clusters, one for each parameter.
        If the set has no parameters, nothing is returned (since empty clusters
        are not allowed).
        """
        dataset = self.get_dataset(c)
        names = dataset.get_param_names()
        params = tuple((name, dataset.get_parameter(name)) for name in names)
        key = self.context_key(c)
        dataset.param_listeners.add(key)  # send a message when new parameters are added
        if len(params):
            return params

    @setting(200, "add comment", comment=["s"], user=["s"], returns=[""])
    def add_comment(self, c, comment, user="anonymous"):
        """
        Add a comment to the current dataset.
        """
        dataset = self.get_dataset(c)
        return dataset.add_comment(user, comment)

    @setting(
        201,
        "get comments",
        limit=["w"],
        start_over=["b"],
        returns=["*(t, s{user}, s{comment})"],
    )
    def get_comments(self, c, limit=None, start_over=False):
        """
        Get comments for the current dataset.
        """
        dataset = self.get_dataset(c)
        c["commentpos"] = 0 if start_over else c["commentpos"]
        comments, c["commentpos"] = dataset.get_comments(limit, c["commentpos"])
        key = self.context_key(c)
        dataset.keep_streaming_comments(key, c["commentpos"])
        return comments

    @setting(
        300,
        "update tags",
        tags=["s", "*s"],
        dirs=["s", "*s"],
        datasets=["s", "*s"],
        returns="",
    )
    def update_tags(self, c, tags, dirs, datasets=None):
        """
        Update the tags for the specified directories and datasets.

        If a tag begins with a minus sign '-' then the tag (everything
        after the minus sign) will be removed.  If a tag begins with '^'
        then it will be toggled from its current state for each entry
        in the list.  Otherwise it will be added.

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

    @setting(
        301, "get tags", dirs=["s", "*s"], datasets=["s", "*s"], returns="*(s*s)*(s*s)"
    )
    def get_tags(self, c, dirs, datasets):
        """
        Get tags for directories and datasets in the current dir.
        """
        sess = self.get_session(c)
        if isinstance(dirs, str):
            dirs = [dirs]
        if isinstance(datasets, str):
            datasets = [datasets]
        return sess.get_tags(dirs, datasets)


class DataVaultMultiHead(DataVault):
    """
    Data Vault server with additional settings for running multi-headed.

    One instance will be created for each manager we connect to, and new
    instances will be created when we reconnect after losing a connection.
    """

    def __init__(self, host, port, password, hub, session_store):
        DataVault.__init__(self, session_store)
        self.host = host
        self.port = port
        self.password = password
        self.hub = hub
        self.alive = False

    def initServer(self):
        DataVault.initServer(self)
        # let the DataVaultHost know that we connected
        self.hub.connect(self)
        self.alive = True
        self.keepalive_timer = LoopingCall(self.keepalive)
        self.onShutdown().addBoth(self.end_keepalive)
        self.keepalive_timer.start(120)

    def end_keepalive(self, *ignored):
        # stopServer is only called when the whole application shuts down.
        # We need to manually use the onShutdown() callback
        self.keepalive_timer.stop()

    @inlineCallbacks
    def keepalive(self):
        print("sending keepalive to {}:{}".format(self.host, self.port))
        try:
            yield self.client.manager.echo("ping")
        except:
            pass  # We don't care about errors, dropped connections will be recognized automatically

    def context_key(self, c):
        return ExtendedContext(self, c.ID)

    @setting(401, "get servers", returns="*(swb)")
    def get_servers(self, c):
        """
        Returns the list of running servers as tuples of (host, port, connected?).
        """
        rv = []
        for s in self.hub:
            host = s.host
            port = s.port
            running = s.connected
            print("host: %s port: %s running: %s" % (host, port, running))
            rv.append((host, port, running))
        return rv

    @setting(402, "add server", host="s", port="w", password="s")
    def add_server(self, c, host, port=None, password=None):
        """
        Add new server to the list.
        """
        port = port if port is not None else self.port
        password = password if password is not None else self.password
        self.hub.add_server(host, port, password)

    @setting(403, "Ping Managers")
    def ping_managers(self, c):
        self.hub.ping()

    @setting(404, "Kick Managers", host_regex="s", port="w")
    def kick_managers(self, c, host_regex, port=0):
        self.hub.kick(host_regex, port)

    @setting(405, "Reconnect", host_regex="s", port="w")
    def reconnect(self, c, host_regex, port=0):
        self.hub.reconnect(host_regex, port)

    @setting(406, "Refresh Managers")
    def refresh_managers(self, c):
        return self.hub.refresh_managers()


class ExtendedContext(object):
    """
    This is an extended context that contains the manager.  This prevents
    multiple contexts with the same client ID from conflicting if they are
    connected to different managers.
    """

    def __init__(self, server, ctx):
        self.__server = server
        self.__ctx = ctx

    @property
    def server(self):
        return self.__server

    @property
    def context(self):
        return self.__ctx

    def __eq__(self, other):
        return (self.context == other.context) and (self.server == other.server)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.context) ^ hash(self.server.host) ^ self.server.port
