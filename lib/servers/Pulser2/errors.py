from labrad.types import Error


class DDSAccessLockedError(Error):

    def __init__(self):
        super(DDSAccessLockedError, self).__init__(
            msg="DDS Access Locked: running a pulse sequence", code=1
        )


class MissingSequenceError(Exception):
    pass
