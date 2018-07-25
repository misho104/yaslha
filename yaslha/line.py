import enum
import re
from typing import cast, Optional, Union, Tuple, List

import yaslha.exceptions


KeyType = Union[None, int, Tuple[int, ...]]
ValueType = Union[int, float, str, List[str]]   # SPINFO/DCINFO 3 and 4 may be multiple
ChannelType = Tuple[int, ...]

StrFloat = Union[str, float]
StrInt = Union[str, int]

FLOAT = r'[+-]?(?:\d+\.\d*|\d+|\.\d+)(?:[de][+-]\d+)?'
INT = r'[+-]?\d+'
NAME = r'[a-z0-9]+'
INFO = r'[^#]+'
SEP = r'\s+'
TAIL = r'\s*(?:\#(?P<comment>.*))?'

RE_INT = re.compile(f'^{INT}$', re.IGNORECASE)
RE_FLOAT = re.compile(f'^{FLOAT}$', re.IGNORECASE)


def cap(regexp: str, name: str) -> str:
    return f'(?P<{name}>{regexp})'


def possible(regexp) -> str:
    return f'(?:{regexp})?'


def guess_key_type(value: KeyType) -> KeyType:
    if isinstance(value, str) and RE_INT.match(value):
        return int(value)
    return value


def guess_type(value: ValueType) -> ValueType:
    if isinstance(value, str):
        if RE_INT.match(value):
            return int(value)
        elif RE_FLOAT.match(value):
            return float(value)
    return value


class AbsLine:
    IN = NotImplemented   # type: str
    IN_PATTERN = None     # filled later

    def __init__(self, *args, **kwargs)->None:
        self.key = NotImplemented
        self.value = NotImplemented
        self.comment = NotImplemented

    @classmethod
    def construct(cls, line: str)->Optional['AbsLine']:
        if cls.IN_PATTERN is None:
            # explicitly include ^ and $
            cls.IN_PATTERN = re.compile(f'^{cls.IN}$', re.IGNORECASE)
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
    IN = cap('\s*(#.*)?', 'line')

    def __init__(self, line: str)->None:
        self.line = line  # type: str

    @property
    def line(self)->str:
        return self._line

    @line.setter
    def line(self, value: str):
        if not value.startswith('#'):
            value = '# ' + value.strip()
        self._line = value.rstrip()


class BlockLine(AbsLine):
    IN = 'Block' + SEP + cap(NAME, 'name') + possible(SEP + 'Q=\s*' + cap(FLOAT, 'q')) + TAIL

    def __init__(self, name: str, q: Optional[StrFloat]=None, comment: str='')->None:
        self.name = name.upper()
        self.q = float(q) if q is not None else None
        self.comment = comment or ''


class DecayBlockLine(AbsLine):
    """A line with format ('DECAY',1x,I9,3x,1P,E16.8,0P,3x,'#',1x,A)"""
    IN = 'DECAY' + SEP + cap(INT, 'pid') + SEP + cap(FLOAT, 'width') + TAIL

    def __init__(self, pid: StrInt, width: StrFloat, comment: str='')->None:
        self.pid = int(pid)
        self.width = float(width)
        self.comment = comment or ''

    def __str__(self)->str:
        return f'DECAY {self.pid:>9}   {self.width:16.8e}   # {self.comment}'.rstrip()


class InfoLine(AbsLine):
    """A line with format(1x,I5,3x,A).

    Note that this pattern is not exclusive; "IndexLine"s also match
    this pattern. So this is not a subclass of ValueLine.
    """

    IN = '\s*' + cap(INT, 'key') + SEP + cap(INFO, 'value') + TAIL

    def __init__(self, key: KeyType, value: Union[str, List[str]], comment: Union[str, List[str]]='')->None:
        try:
            self.key = int(key)  # type: ignore
        except TypeError:
            raise yaslha.exceptions.InvalidInfoBlockError(key)
        self.value = list()      # type: List[str]
        self.comment = list()    # type: List[str]
        self.append(value, comment)

    def append(self, value: Union[str, List[str]], comment: Union[str, List[str]]='')->None:
        self.value += value if isinstance(value, list) else [value.strip()]
        self.comment += comment if isinstance(comment, list) else [(comment or '').strip()]


class ValueLine(AbsLine):
    def __init__(self, key: KeyType, value: ValueType, comment: str='')->None:
        self.key = guess_key_type(key)
        self.value = guess_type(value)
        self.comment = comment or ''


class NoIndexLine(ValueLine):
    """A line with format(9x, 1P, E16.8, 0P, 3x, '#', 1x, A)"""

    IN = '\s*' + cap(FLOAT, 'value') + TAIL

    def __init__(self, value: float, comment: str='')->None:
        super().__init__(None, value, comment)


class OneIndexLine(ValueLine):
    """A line with format(1x,I5,3x,1P,E16.8,0P,3x,'#',1x,A)"""

    IN = '\s*' + cap(INT, 'index') + SEP + cap(FLOAT, 'value') + TAIL

    def __init__(self, index: StrInt, value: ValueType, comment: str='')->None:
        super().__init__(int(index), guess_type(value), comment)


class TwoIndexLine(ValueLine):
    """A line with format(1x,I2,1x,I2,3x,1P,E16.8,0P,3x,'#',1x,A)"""

    IN = '\s*' + cap(INT, 'i1') + SEP + cap(INT, 'i2') + SEP + cap(FLOAT, 'value') + TAIL

    def __init__(self, i1: StrInt, i2: StrInt, value: ValueType, comment: str='')->None:
        super().__init__((int(i1), int(i2)), guess_type(value), comment)


class ThreeIndexLine(ValueLine):
    """A line with format(1x,I2,1x,I2,1x,I2,3x,1P,E16.8,0P,3x,'#',1x,A)"""

    IN = '\s*' + cap(INT, 'i1') + SEP + cap(INT, 'i2') + SEP + cap(INT, 'i3') + SEP + cap(FLOAT, 'value') + TAIL

    def __init__(self, i1: int, i2: int, i3: int, value: ValueType, comment: str='')->None:
        super().__init__((int(i1), int(i2), int(i3)), guess_type(value), comment)


class DecayLine(ValueLine):
    """A line with format (3x,1P,E16.8,0P,3x,I2,3x,N (I9,1x),2x,'#',1x,A)."""
    IN = '\s*' + cap(FLOAT, 'br') + SEP + cap(INT, 'nda') + SEP + cap(r'[0-9\s+-]+', 'daughters') + TAIL

    def __init__(
            self, br: float, nda: Optional[int]=0,
            daughters: Optional[str]='',
            channel: Optional[ChannelType]=None,
            comment: str='')->None:
        # nda is not used.
        if not (daughters or channel):
            raise ValueError('Neither string nor set is specified')
        elif daughters and channel:
            raise ValueError('Both string and set is specified')
        elif daughters:
            self.key = tuple(int(pid) for pid in re.split(r'\s+', daughters.strip()))
        else:
            self.key = channel
        self.value = float(br)
        self.comment = comment or ''


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
