"""Helpers for `yaslha.line` module."""

import re
from typing import Any, List, Sequence, TypeVar, Union, cast

import numpy

T = TypeVar("T", str, List[str])

# -----------------------------------------------------------------------------
# type definitions
# -----------------------------------------------------------------------------
"""Type for keys of ordinary blocks."""
KeyType = Union[None, int, Sequence[int]]
"""Type for values of ordinary blocks."""
ValueType = float  # typing.int is included in typing.float
"""Type for keys of info blocks."""
InfoKeyType = int
""""Type for values of INFO blocks."""
InfoValueType = str
"""Type for keys of decay blocks."""
DecayKeyType = Sequence[int]
"""Type for values of decay blocks."""
DecayValueType = float

# -----------------------------------------------------------------------------
# regular expressions
# -----------------------------------------------------------------------------
"""Regexp for float data in SLHA file."""
FLOAT = r"[+-]?(?:\d+\.\d*|\d+|\.\d+)(?:[deDE][+-]\d+)?"
"""Regexp for integer data in SLHA file."""
INT = r"[+-]?\d+"
"""Regexp for block names in SLHA file."""
NAME = r"[A-Za-z][A-Za-z0-9]*"
"""Regexp for values in INFO blocks."""
INFO = r"[^#]+"
"""Regexp for separators in SLHA file."""
SEP = r"\s+"
"""Regexp for tails of SLHA data line, capturing comment."""
TAIL = r"\s*(?:\# ?(?P<comment>.*))?"

"""Compiled regexp for float data in SLHA file."""
RE_INT = re.compile("^" + INT + "$")
"""Compiled regexp for int data in SLHA file."""
RE_FLOAT = re.compile("^" + FLOAT + "$")


def cap(regexp: str, name: str) -> str:
    """Return capture-pattern of REGEXP string."""
    return "(?P<{}>{})".format(name, regexp)


def possible(regexp: str) -> str:
    """Return possible pattern ```?``` of REGEXP string."""
    return "(?:{})?".format(regexp)


# -----------------------------------------------------------------------------
# other utility
# -----------------------------------------------------------------------------
def _float(obj: Any) -> float:
    """Convert any values to float if possible, otherwise raise an error."""
    if isinstance(obj, str):
        obj = obj.replace("d", "e").replace("D", "E")
    return float(obj)


def to_number(v: Any) -> float:
    """Convert any object to float or int depending on the expression."""
    if isinstance(v, float) or isinstance(v, int):
        return v
    elif isinstance(v, str):
        if RE_INT.match(v):
            return int(v)
        elif RE_FLOAT.match(v):
            return _float(v)
        raise ValueError("to_number failed: %s" % v)
    elif isinstance(v, numpy.ndarray) and v.ndim == 0:
        return cast(float, v.__pos__())
    else:
        return to_number(str(v))


def number_to_str(v: float, int_format: str = "d", float_format: str = "16.8e") -> str:
    """Convert int or float to string."""
    if isinstance(v, int):
        return ("{:" + int_format + "}").format(v)
    elif isinstance(v, float):
        return ("{:" + float_format + "}").format(v)
    else:
        raise TypeError(v)


def format_comment(comment: T, add_sharp: bool = True, strip: bool = True) -> T:
    """Format a comment string."""
    if isinstance(comment, str):
        comment = comment.strip() if strip else comment.rstrip()
        if add_sharp and not comment.startswith("#"):
            return "# " + comment if comment else "#"
        else:
            return comment
    else:
        return [format_comment(c, add_sharp, strip) for c in comment]
