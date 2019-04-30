"""Module to describe each type of lines.

The line hierarchy is given by:

- AbsLine
  - BlockHeadLine
  - DecayHeadLine
  - InfoLine
  - ValueLine
    - NoIndexLine
    - OneIndexLine
    - TwoIndexLine
    - ThreeIndexLine
  - DecayLine
  - CommentLine
"""
import collections.abc as abc
import logging
import re
from abc import ABCMeta, abstractmethod
from typing import (
    Any,
    ClassVar,
    List,
    Optional,
    Pattern,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

from yaslha._line import (
    FLOAT,
    INFO,
    INT,
    NAME,
    SEP,
    TAIL,
    DecayKeyType,
    DecayValueType,
    InfoKeyType,
    InfoValueType,
    KeyType,
    ValueType,
    _float,
    cap,
    format_comment,
    possible,
    to_number,
)

logger = logging.getLogger(__name__)

OS = Union[str, None]
SInt = Union[str, int]
SFloat = Union[str, float]
SValue = Union[str, ValueType]

CT = TypeVar("CT", str, List[str])
LT = TypeVar("LT", bound="AbsLine")
LT2 = TypeVar("LT2", bound="ValueLine")


class LineOutputOption:
    """Class to hold all the options on dumping lines."""

    # type comment for python 3.6
    # block_str: str  # the string "BLOCK" for block head
    # decay_str: str  # the string "DECAY" for decay-block head
    # comment: bool  # whether to output line-end comments
    # pre_comment: bool  # whether to output pre-line comments
    # float_lower: bool  # letter E for float numbers

    def __init__(self) -> None:
        self.block_str = "Block"
        self.decay_str = "Decay"
        self.comment = True
        self.pre_comment = True
        self.float_lower = False


class AbsLine(metaclass=ABCMeta):
    """Abstract class for SLHA-line like objects."""

    output_option = LineOutputOption()  # type: ClassVar[LineOutputOption]

    _pattern = NotImplemented  # type: ClassVar[str]
    _pattern_compiled = None  # type: ClassVar[Optional[Pattern[str]]]

    @classmethod
    def pattern(cls) -> Pattern[str]:
        """Return a regexp pattern matching a SLHA line for the type."""
        if cls._pattern_compiled is None:
            cls._pattern_compiled = re.compile("^{}$".format(cls._pattern), re.I)
        return cls._pattern_compiled

    @classmethod
    def construct(cls: Type[LT], line: str) -> "Optional[LT]":
        """Construct an object from a line if it maches the pattern."""
        match = cls.pattern().match(line)
        if match:
            return cast(LT, cls(**match.groupdict()))
        else:
            return None

    @abstractmethod
    def __init__(self, **kwargs: Any) -> None:
        self.comment = NotImplemented  # type: str
        self.pre_comment = NotImplemented  # type: List[str]

    # from/to object/string representation
    def __str__(self) -> str:
        return self._to_slha(self.output_option)

    def to_slha(self, option: Optional[LineOutputOption] = None) -> List[str]:
        """Return the lines for SLHA-format, including pre-comments."""
        opt = option or self.output_option
        lines = self._format_pre_comment(opt)  # pre comment
        lines.append(self._to_slha(opt))  # line itself
        return lines

    def dump(self) -> List[SFloat]:
        """Return a list representing the line."""
        return self._dump()

    @classmethod
    def from_dump(cls: Type[LT], dump: Sequence[Any], **kw: Any) -> LT:
        """Return an object from dumped value."""
        return cls._from_dump(dump, **kw)

    # implementation
    @abstractmethod
    def _to_slha(self, opt: LineOutputOption) -> str:
        pass

    @abstractmethod
    def _dump(self) -> List[SFloat]:
        pass

    @classmethod
    @abstractmethod
    def _from_dump(cls: Type[LT], dump: Sequence[Any], **kw: Any) -> LT:
        pass

    # comment handling (type declaration for python 3.6)
    # comment: str
    # pre_comment: List[str]

    def _format_comment(self, opt: LineOutputOption) -> str:
        """Return the comment formatted for SLHA line."""
        if opt.comment:
            return format_comment(self.comment, add_sharp=True, strip=True)
        else:
            return "#"

    def _format_pre_comment(self, opt: LineOutputOption) -> List[str]:
        """Return the pre-comment formatted as SLHA lines."""
        if opt.pre_comment:
            return [
                format_comment(c, add_sharp=True, strip=False) for c in self.pre_comment
            ]
        else:
            return []

    @abstractmethod
    def _dump_comment(self) -> List[List[SFloat]]:
        pass

    # helper method
    @classmethod
    def _num_to_str(cls, opt, v, allow_int=False):
        # type: (LineOutputOption, float, bool)->str
        if isinstance(v, int) and allow_int:
            return str(v)
        f = "{:16.8e}" if opt.float_lower else "{:16.8E}"
        return f.format(v)


class BlockHeadLine(AbsLine):
    """Line for block header."""

    _pattern = (
        "Block"
        + SEP
        + cap(NAME, "name")
        + possible(SEP + r"Q=\s*" + cap(FLOAT, "q"))
        + TAIL
    )

    def __init__(self, name, q=None, comment=None):
        # type: (str, Optional[SFloat], OS)->None
        self.name = name
        self.q = None if q is None else _float(q)
        self.comment = comment or ""
        self.pre_comment = []

    @property
    def name(self) -> str:
        """Return name in upper case."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value.upper()

    def _to_slha(self, opt: LineOutputOption) -> str:
        if self.q is None:
            name = " {:17}   ".format(self.name)
        else:
            name = " {} Q={}   ".format(self.name, self._num_to_str(opt, self.q))
        return (opt.block_str + name + self._format_comment(opt)).rstrip()

    def _dump(self) -> List[SFloat]:
        return [] if self.q is None else ["Q=", self.q]

    @classmethod
    def _from_dump(cls: Type[LT], dump: Sequence[Any], **kw: Any) -> LT:
        name = str(kw.get("name"))
        if not name or len(kw) > 1:
            raise ValueError(kw)
        if len(dump) == 0:
            return cast(LT, cls(name=name))
        elif len(dump) == 2:
            if isinstance(dump[0], str) and dump[0].strip().upper() == "Q=":
                return cast(LT, cls(name=name, q=_float(dump[1])))
        raise ValueError(dump)

    def _dump_comment(self) -> List[List[SFloat]]:
        comments = [
            ["pre", "HEAD", c] for c in self.pre_comment
        ]  # type: List[List[SFloat]]
        if self.comment:
            comments.append(["HEAD", self.comment])
        return comments


class DecayHeadLine(AbsLine):
    """A line with format ``('DECAY',1x,I9,3x,1P,E16.8,0P,3x,'#',1x,A)``."""

    _pattern = "Decay" + SEP + cap(INT, "pid") + SEP + cap(FLOAT, "width") + TAIL

    def __init__(self, pid: SInt, width: SFloat, comment: OS = None) -> None:
        self.pid = int(pid)
        self.width = _float(width)
        self.comment = comment or ""
        self.pre_comment = []

    def _to_slha(self, opt: LineOutputOption) -> str:
        return "{decay} {pid:>9}   {width}   {comment}".format(
            decay=opt.decay_str,
            pid=self.pid,
            width=self._num_to_str(opt, self.width),
            comment=self._format_comment(opt),
        )

    def _dump(self) -> List[SFloat]:
        return [self.width]

    @classmethod
    def _from_dump(cls: Type[LT], dump: Sequence[Any], **kw: Any) -> LT:
        pid = kw.get("pid")
        if not pid or len(kw) > 1:
            raise ValueError(kw)
        elif len(dump) == 1:
            return cast(LT, cls(pid=int(pid), width=_float(dump[0])))
        raise ValueError(dump)

    def _dump_comment(self) -> List[List[SFloat]]:
        comments = [
            ["pre", "HEAD", c] for c in self.pre_comment
        ]  # type: List[List[SFloat]]
        if self.comment:
            comments.append(["HEAD", self.comment])
        return comments


class InfoLine(AbsLine):
    """Class for lines of INFO blocks.

    An info-block line is given by ``format(1x,I5,3x,A)``, which is not
    exclusive and matches other patterns. This class accept multi-lines, and
    thus values are List[str] and comments are multi-lined string, internally
    kept as List[str].
    """

    _pattern = r"\s*" + cap(INT, "key") + SEP + cap(INFO, "value") + TAIL

    def __init__(self, key, value, comment=None):
        # type: (InfoKeyType, InfoValueType, OS)->None
        self.key = int(key)  # type: InfoKeyType
        self.value = value.rstrip()  # type: InfoValueType
        self.comment = comment or ""
        self.pre_comment = []

    def _to_slha(self, opt: LineOutputOption) -> str:
        return " {:5d}   {:16}   {}".format(
            self.key, self.value, self._format_comment(opt)
        )

    def _dump(self) -> List[SFloat]:
        return [self.key, self.value]

    @classmethod
    def _from_dump(cls: Type[LT], dump: Sequence[Any], **kw: Any) -> LT:
        if kw:
            raise ValueError(kw)
        if len(dump) == 2:
            return cast(LT, cls(int(dump[0]), value=str(dump[1])))
        raise ValueError(dump)

    def _dump_comment(self) -> List[List[SFloat]]:
        comments = [
            ["pre", self.key, c] for c in self.pre_comment
        ]  # type: List[List[SFloat]]
        if self.comment:
            comments.append([self.key, self.comment])
        return comments


class ValueLine(AbsLine, metaclass=ABCMeta):
    """Abstract class for value lines in ordinary blocks."""

    @abstractmethod
    def __init__(self, key: KeyType, value: SValue, comment: OS = None) -> None:
        self.key = key  # type: KeyType
        self.value = to_number(value)  # type: ValueType
        self.comment = comment or ""
        self.pre_comment = []

    @classmethod
    def new(cls: Type[LT2], key: KeyType, value: SValue, comment: OS = None) -> LT2:
        """Construct line object according to the type of key.

        The resulting object is an instance of a subclass of `ValueLine` but
        not `DecayLine`.
        """
        if key is None:
            return cast(LT2, NoIndexLine(value, comment))
        elif isinstance(key, int):
            return cast(LT2, OneIndexLine(key, value, comment))
        elif isinstance(key, abc.Sequence) and all(isinstance(i, int) for i in key):
            if len(key) == 1:
                return cast(LT2, OneIndexLine(key[0], value, comment))
            elif len(key) == 2:
                return cast(LT2, TwoIndexLine(key[0], key[1], value, comment))
            elif len(key) == 3:
                return cast(LT2, ThreeIndexLine(key[0], key[1], key[2], value, comment))
        raise TypeError(key)

    def _to_slha(self, opt: LineOutputOption) -> str:
        if self.key is None:
            k = "      "
        elif isinstance(self.key, int):
            k = " {:5d}".format(self.key)
        else:
            k = "{:6}".format("".join(" {:2d}".format(k) for k in self.key))
        if isinstance(self.value, int):
            v = "{:10}      ".format(self.value)
        else:
            v = self._num_to_str(opt, self.value, False)
        return "{}   {}   {}".format(k, v, self._format_comment(opt))

    def _dump(self) -> List[SFloat]:
        if self.key is None:
            return [self.value]
        elif isinstance(self.key, int):
            return [self.key, self.value]
        elif isinstance(self.key, abc.Sequence):
            return [*self.key, self.value]
        raise TypeError(self.key)

    @classmethod
    def _from_dump(cls: Type[LT2], dump: Sequence[Any], **kw: Any) -> LT2:
        if kw:
            raise ValueError(kw)
        if len(dump) == 0:
            raise ValueError(dump)
        elif len(dump) == 1:
            return cls.new(key=None, value=dump[-1])
        elif len(dump) == 2:
            return cls.new(key=int(dump[0]), value=dump[-1])
        else:
            return cls.new(key=tuple(int(k) for k in dump[:-1]), value=dump[-1])

    def _dump_comment(self) -> List[List[SFloat]]:
        if self.key is None:
            key_tuple = []  # type: Sequence[int]
        elif isinstance(self.key, int):
            key_tuple = [self.key]
        elif isinstance(self.key, abc.Sequence):
            key_tuple = self.key
        comments = [
            ["pre", *key_tuple, c] for c in self.pre_comment
        ]  # type: List[List[SFloat]]
        if self.comment:
            comments.append([*key_tuple, self.comment])
        return comments


class NoIndexLine(ValueLine):
    """A line with ``format(9x, 1P, E16.8, 0P, 3x, '#', 1x, A)``."""

    _pattern = r"\s*" + cap(FLOAT, "value") + TAIL

    def __init__(self, value, comment=None):
        # type: (SValue, OS)->None
        super().__init__(None, value, comment)


class OneIndexLine(ValueLine):
    """A line with ``format(1x,I5,3x,1P,E16.8,0P,3x,'#',1x,A)``."""

    _pattern = r"\s*" + cap(INT, "i") + SEP + cap(FLOAT, "value") + TAIL

    def __init__(self, i, value, comment=None):
        # type: (SInt, SValue, OS)->None
        super().__init__(int(i), value, comment)


class TwoIndexLine(ValueLine):
    """A line with ``format(1x,I2,1x,I2,3x,1P,E16.8,0P,3x,'#',1x,A)``."""

    _pattern = (
        r"\s*"
        + cap(INT, "i1")
        + SEP
        + cap(INT, "i2")
        + SEP
        + cap(FLOAT, "value")
        + TAIL
    )

    def __init__(self, i1, i2, value, comment=None):
        # type: (SInt, SInt, SValue, OS)->None
        super().__init__((int(i1), int(i2)), value, comment)


class ThreeIndexLine(ValueLine):
    """A line with ``format(1x,I2,1x,I2,1x,I2,3x,1P,E16.8,0P,3x,'#',1x,A)``."""

    _pattern = (
        r"\s*"
        + cap(INT, "i1")
        + SEP
        + cap(INT, "i2")
        + SEP
        + cap(INT, "i3")
        + SEP
        + cap(FLOAT, "value")
        + TAIL
    )

    def __init__(self, i1, i2, i3, value, comment=None):
        # type: (SInt, SInt, SInt, SValue, OS)->None
        super().__init__((int(i1), int(i2), int(i3)), value, comment)


class DecayLine(ValueLine):
    """A decay line ``(3x,1P,E16.8,0P,3x,I2,3x,N (I9,1x),2x,'#',1x,A)``."""

    _pattern = (
        r"\s*"
        + cap(FLOAT, "br")
        + SEP
        + cap(INT, "nda")
        + SEP
        + cap(r"[0-9\s+-]+", "channel")
        + TAIL
    )

    def __init__(self, br, channel, nda=None, comment=None):
        # type: (Union[str, DecayValueType], Union[str, DecayKeyType], Any, OS)->None
        if isinstance(channel, str):
            self.key = tuple(int(p) for p in re.split(r"\s+", channel.strip()))
        else:
            self.key = channel  # type: DecayKeyType
        self.value = _float(br)  # type: DecayValueType

        self.comment = comment or ""
        self.pre_comment = []

    # provide synonym
    @property
    def br(self) -> DecayValueType:
        """Return the branching ratio."""
        return self.value

    @br.setter
    def br(self, br: DecayValueType) -> None:
        self.value = br

    def _to_slha(self, opt: LineOutputOption) -> str:
        pids = "".join("{:9d} ".format(pid) for pid in self.key)
        return "   {}   {:2d}   {}  {}".format(
            self._num_to_str(opt, self.br),
            len(self.key),
            pids,
            self._format_comment(opt),
        )

    def _dump(self) -> List[SFloat]:
        result = [self.br, len(self.key)]  # type: List[SFloat]
        result.extend(self.key)
        return result

    @classmethod
    def _from_dump(cls: Type[LT2], dump: Sequence[Any], **kw: Any) -> LT2:
        if kw:
            raise ValueError(kw)
        if len(dump) >= 4:
            br, nda = _float(dump[0]), int(dump[1])
            pids = tuple(int(p) for p in dump[2:])
            if nda == len(pids):
                return cast(LT2, cls(br=br, channel=pids))
        raise ValueError(dump)

    def _dump_comment(self) -> List[List[SFloat]]:
        comments = [["pre", c] for c in self.pre_comment]  # type: List[List[SFloat]]
        if self.comment:
            comments.append([self.comment])
        for c in comments:
            c.extend(self.key)
        return comments


class CommentLine(AbsLine):
    """Comment line.

    This object is prepared for compatibility and not intended to be inserted
    in blocks or decay-blocks; therefore dumping methods are not implemented.
    """

    _pattern = r"\s*(?P<comment>\#.*)"

    def __init__(self, comment: OS = None) -> None:
        self.comment = (comment or "").rstrip()
        self.pre_comment = []

    def _to_slha(self, opt: LineOutputOption) -> str:
        raise NotImplementedError

    def _dump(self) -> List[SFloat]:
        raise NotImplementedError

    @classmethod
    def _from_dump(cls: Type[LT], dump: Sequence[Any], **kw: Any) -> LT:
        raise NotImplementedError

    def _dump_comment(self) -> List[List[SFloat]]:
        raise NotImplementedError
