from labrad import types


class NoDatasetError(types.Error):
    """Please open a dataset first."""
    code = 2


class DatasetNotFoundError(types.Error):
    code = 3

    def __init__(self, name):
        self.msg = "Dataset '%s' not found!" % name


class DirectoryExistsError(types.Error):
    code = 4

    def __init__(self, name):
        self.msg = "Directory '%s' already exists!" % name


class DirectoryNotFoundError(types.Error):
    code = 5


class EmptyNameError(types.Error):
    """Names of directories or keys cannot be empty"""
    code = 6

    def __init__(self, path):
        self.msg = "Directory %s does not exist!" % (path,)


class ReadOnlyError(types.Error):
    """Points can only be added to datasets created with 'new' or opened with
    'open_appendable'."""
    code = 7


class BadDataError(types.Error):
    code = 8

    def __init__(self, varcount, gotcount):
        requires_message = 'Dataset requires %d values per datapoint not %d.'
        self.msg = requires_message % (varcount, gotcount)


class BadParameterError(types.Error):
    code = 9

    def __init__(self, name):
        self.msg = "Parameter '%s' not found." % name


class ParameterInUseError(types.Error):
    code = 10

    def __init__(self, name):
        self.msg = "Already a parameter called '%s'." % name


class AdditionalHeaderInUseError(types.Error):
    code = 11

    def __init__(self, header_name, name):
        self.msg = "Already a value called '%s' in header '%s'." % (name, header_name)


class BadAdditionalHeaderError(types.Error):
    code = 12

    def __init__(self, header_name, name):
        self.msg = "'%s' in header '%s' not found." % (name, header_name)
