
class Globals:
    # location of repository will get loaded from the registry
    DATADIR = None
    PRECISION = 15  # digits of precision to use when saving data
    DATA_FORMAT = '%%.%dG' % PRECISION
    STRING_FORMAT = '%s'
    FILE_TIMEOUT = 60  # how long to keep datafiles open if not accessed
    DATA_TIMEOUT = 300  # how long to keep data in memory if not accessed
    TIME_FORMAT = '%Y-%m-%d, %H:%M:%S'
