import enum
import re
from typing import cast, Any, Optional, Union, List, Pattern  # noqa: F401

import yaslha.exceptions
from yaslha.utility import _float, KeyType, ValueType, ChannelType


StrFloat = Union[str, float]
StrInt = Union[str, int]

FLOAT = r'[+-]?(?:\d+\.\d*|\d+|\.\d+)(?:[de][+-]\d+)?'
INT = r'[+-]?\d+'
NAME = r'[a-z0-9]+'
INFO = r'[^#]+'
SEP = r'\s+'
TAIL = r'\s*(?:\#(?P<comment>.*))?'

RE_INT = re.compile('^' + INT + '$', re.IGNORECASE)
RE_FLOAT = re.compile('^' + FLOAT + '$', re.IGNORECASE)


def cap(regexp, name):
    # type: (str, str)->str
    """Returns capture-pattern of REGEXP string."""
    return '(?P<{}>{})'.format(name, regexp)


def possible(regexp):
    # type: (str)->str
    return '(?:{})?'.format(regexp)


def guess_key_type(value):
    # type: (KeyType)->KeyType
    if isinstance(value, str) and RE_INT.match(value):
        return int(value)
    return value


def guess_type(value):
    # type: (ValueType)->ValueType
    if isinstance(value, str):
        if RE_INT.match(value):
            return int(value)
        elif RE_FLOAT.match(value):
            return _float(value)
    return value


class AbsLine:
    IN = NotImplemented  # type: str
    IN_PATTERN = None    # type: Pattern[str]
    # IN_PATTERN is filled later

    def __init__(self, **kwargs):
        # type: (Any)->None
        self.key = NotImplemented       # type: KeyType
        self.value = NotImplemented     # type: ValueType
        self.comment = NotImplemented   # type: Union[str, List[str]]

    @classmethod
    def construct(cls, line):
        # type: (str)->Optional[AbsLine]
        if cls.IN_PATTERN is None:
            # explicitly include ^ and $
            cls.IN_PATTERN = re.compile('^{}$'.format(cls.IN), re.IGNORECASE)
        match = cls.IN_PATTERN.match(line)
        if match:
            return cls(**match.groupdict())
        else:
            return None


class CommentLine(AbsLine):
    """A comment line.

    We allow preceding spaces and 'empty' lines as input, while do not
    allow them as output because many other parsers do not like them.
    """
    IN = cap(r'\s*(#.*)?', 'line')

    def __init__(self, line):
        # type: (str)->None
        self.line = line  # type: str

    @property
    def line(self):
        # type: ()->str
        return self._line

    @line.setter
    def line(self, value):
        # type: (str)->None
        if not value.startswith('#'):
            value = '# ' + value.strip()
        self._line = value.rstrip()


class BlockLine(AbsLine):
    IN = 'Block' + SEP + cap(NAME, 'name') + possible(SEP + r'Q=\s*' + cap(FLOAT, 'q')) + TAIL

    def __init__(self, name: str, q: Optional[StrFloat] = None, comment: str = '')->None:
        self.name = name.upper()
        self.q = _float(q) if q is not None else None
        self.comment = (comment or '').strip()   # type: str


class DecayBlockLine(AbsLine):
    """A line with format ('DECAY',1x,I9,3x,1P,E16.8,0P,3x,'#',1x,A)"""
    IN = 'DECAY' + SEP + cap(INT, 'pid') + SEP + cap(FLOAT, 'width') + TAIL

    def __init__(self, pid: StrInt, width: StrFloat, comment: str = '')->None:
        self.pid = int(pid)
        self.width = _float(width)
        self.comment = (comment or '').strip()   # type: str

    def __str__(self):
        # type: ()->str
        return 'DECAY {:>9}   {:16.8e}   # {}'.format(self.pid, self.width, self.comment.lstrip).rstrip()


class InfoLine(AbsLine):
    """A line with format(1x,I5,3x,A).

    Note that this pattern is not exclusive; "IndexLine"s also match
    this pattern. So this is not a subclass of ValueLine.
    """
    IN = r'\s*' + cap(INT, 'key') + SEP + cap(INFO, 'value') + TAIL

    def __init__(self, key: KeyType, value: Union[str, List[str]], comment: Union[str, List[str]] = '')->None:
        try:
            self.key = int(key)  # type: ignore
        except TypeError:
            raise yaslha.exceptions.InvalidInfoBlockError(key)
        self.value = list()        # type: List[str]
        self.comment = list()      # type: List[str]
        self.append(value, comment or '')

    def append(self, value: Union[str, List[str]], comment: Union[str, List[str]] = '')->None:
        value = value if isinstance(value, list) else [value]
        comment = comment if isinstance(comment, list) else [comment]
        for i, v in enumerate(value):
            self.value.append(v.strip())
            self.comment.append(comment[i].strip() if i < len(comment) else '')
        for i in range(len(value), len(comment)):
            if comment[i]:
                raise ValueError('comment has more elements than value.')


class ValueLine(AbsLine):
    def __init__(self, key: KeyType, value: ValueType, comment: str = '')->None:
        self.key = guess_key_type(key)
        self.value = guess_type(value)
        self.comment = (comment or '').strip()  # type: str


class NoIndexLine(ValueLine):
    """A line with format(9x, 1P, E16.8, 0P, 3x, '#', 1x, A)"""
    IN = r'\s*' + cap(FLOAT, 'value') + TAIL

    def __init__(self, value: float, comment: str = '')->None:
        super().__init__(None, value, comment)


class OneIndexLine(ValueLine):
    """A line with format(1x,I5,3x,1P,E16.8,0P,3x,'#',1x,A)"""
    IN = r'\s*' + cap(INT, 'index') + SEP + cap(FLOAT, 'value') + TAIL

    def __init__(self, index: StrInt, value: ValueType, comment: str = '')->None:
        super().__init__(int(index), guess_type(value), comment)


class TwoIndexLine(ValueLine):
    """A line with format(1x,I2,1x,I2,3x,1P,E16.8,0P,3x,'#',1x,A)"""
    IN = r'\s*' + cap(INT, 'i1') + SEP + cap(INT, 'i2') + SEP + cap(FLOAT, 'value') + TAIL

    def __init__(self, i1: StrInt, i2: StrInt, value: ValueType, comment: str = '')->None:
        super().__init__((int(i1), int(i2)), guess_type(value), comment)


class ThreeIndexLine(ValueLine):
    """A line with format(1x,I2,1x,I2,1x,I2,3x,1P,E16.8,0P,3x,'#',1x,A)"""
    IN = r'\s*' + cap(INT, 'i1') + SEP + cap(INT, 'i2') + SEP + cap(INT, 'i3') + SEP + cap(FLOAT, 'value') + TAIL

    def __init__(self, i1: int, i2: int, i3: int, value: ValueType, comment: str = '')->None:
        super().__init__((int(i1), int(i2), int(i3)), guess_type(value), comment)


class DecayLine(ValueLine):
    """A line with format (3x,1P,E16.8,0P,3x,I2,3x,N (I9,1x),2x,'#',1x,A)."""
    IN = r'\s*' + cap(FLOAT, 'br') + SEP + cap(INT, 'nda') + SEP + cap(r'[0-9\s+-]+', 'daughters') + TAIL

    def __init__(self, br, nda=0, daughters='', channel=None, comment=''):  # nda is not used.
        # type: (float, Optional[int], Optional[str], Optional[ChannelType], str)->None
        if daughters and channel:
            raise ValueError('Both string and set is specified')
        elif channel:
            self.key = channel  # type: ChannelType
        elif daughters:
            self.key = tuple(int(pid) for pid in re.split(r'\s+', daughters.strip()))
        else:
            raise ValueError('Neither string nor set is specified')
        self.value = _float(br)   # type: float
        self.comment = (comment or '').strip()


def parse_string(line: str)->Optional[AbsLine]:
    for cls in [
        CommentLine,
        BlockLine,
        NoIndexLine,
        OneIndexLine,
        TwoIndexLine,
        ThreeIndexLine,
        DecayBlockLine,
        DecayLine,
        # InfoLine is excluded by default
    ]:
        obj = cast(AbsLine, cls).construct(line)
        if obj:
            return obj
    return None


def parse_string_in_info_block(line: str)->Optional[AbsLine]:
    for cls in [
        CommentLine,
        BlockLine,
        DecayBlockLine,
        InfoLine
    ]:
        obj = cast(AbsLine, cls).construct(line)
        if obj:
            return obj
    return None


class CommentPosition(enum.Enum):
    Prefix = 'prefix'     # before BLOCK or DECAY line
    Heading = 'heading'   # after BLOCK or DECAY line
    Suffix = 'suffix'     # after the block


CommentPositionType = Union[CommentPosition, KeyType, ChannelType]
