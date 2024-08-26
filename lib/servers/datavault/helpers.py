import os
import re
from globals import Globals
from datetime import datetime

encodings = [
    ("%", "%p"),
    ("/", "%f"),
    ("\\", "%b"),
    (":", "%c"),
    ("*", "%a"),
    ("?", "%q"),
    ('"', "%r"),
    ("<", "%l"),
    (">", "%g"),
    ("|", "%v"),
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
    return os.path.join(Globals.DATADIR, *[ds_encode(d) + ".dir" for d in path[1:]])


# time formatting


def time_to_str(t: datetime) -> str:
    return t.strftime(Globals.TIME_FORMAT)


def time_from_str(s: str) -> datetime:
    return datetime.strptime(s, Globals.TIME_FORMAT)


# variable parsing
re_label = re.compile(r"^([^\[(]*)")  # matches up to the first [ or (
re_legend = re.compile(r"\((.*)\)")  # matches anything inside ()
re_units = re.compile(r"\[(.*)]")  # matches anything inside [ ]


def get_match(pat, s, default=None):
    matches = re.findall(pat, s)
    if len(matches) == 0:
        if default is None:
            raise Exception("Cannot parse '%s'." % s)
        return default
    return matches[0].strip()


def parse_independent(s):
    label = get_match(re_label, s)
    units = get_match(re_units, s, "")
    return label, units


def parse_dependent(s):
    label = get_match(re_label, s)
    legend = get_match(re_legend, s, "")
    units = get_match(re_units, s, "")
    return label, legend, units
