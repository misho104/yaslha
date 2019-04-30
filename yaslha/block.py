"""Block-like object of SLHA data."""


import logging
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from typing import (
    Any,
    ClassVar,
    Generic,
    Iterator,
    List,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

from yaslha._collections import OrderedTupleOrderInsensitiveDict
from yaslha.comment import CommentInterface
from yaslha.line import (
    BlockHeadLine,
    DecayHeadLine,
    DecayKeyType,
    DecayLine,
    DecayValueType,
    InfoKeyType,
    InfoLine,
    InfoValueType,
    KeyType,
    ValueLine,
    ValueType,
)

T = TypeVar("T")

logger = logging.getLogger(__name__)


KT = TypeVar("KT", KeyType, InfoKeyType)
VT = TypeVar("VT", ValueType, InfoValueType)
LT = TypeVar("LT", ValueLine, InfoLine)
CT = TypeVar("CT", str, List[str])
KTG = TypeVar("KTG", KeyType, InfoKeyType, DecayKeyType)


class GenericBlock(Generic[KTG, CT], metaclass=ABCMeta):
    """Block-like object containing comments."""

    @abstractmethod
    def __init__(self) -> None:
        self.head = NotImplemented  # type: Union[BlockHeadLine, DecayHeadLine]
        self._comment = CommentInterface(self)  # type: CommentInterface[KTG, CT]

    @property
    def comment(self) -> "CommentInterface[KTG, CT]":
        """Give the interface to comments."""
        return self._comment

    @abstractmethod
    def _get_comment(self, key: KTG) -> CT:
        pass

    @abstractmethod
    def _get_pre_comment(self, key: KTG) -> List[str]:
        pass

    @abstractmethod
    def _set_comment(self, key: KTG, value: CT) -> None:
        pass

    @abstractmethod
    def _set_pre_comment(self, key: KTG, value: Sequence[str]) -> None:
        pass

    @classmethod
    @overload
    def new(cls, obj: Union[int, DecayHeadLine]) -> "Decay":
        """..."""
        pass

    @classmethod  # noqa: F811
    @overload
    def new(cls, obj: Union[str, BlockHeadLine]) -> Union["Block", "InfoBlock"]:
        """..."""
        pass

    @classmethod  # noqa: F811
    def new(
        cls, obj: Union[int, str, DecayHeadLine, BlockHeadLine]
    ) -> "Union[Block, InfoBlock, Decay]":
        """Create a GenericBlock object according to the argument."""
        if isinstance(obj, int) or isinstance(obj, DecayHeadLine):
            return Decay(obj)
        name = obj.name if isinstance(obj, BlockHeadLine) else obj
        if name.endswith("INFO"):
            return InfoBlock(obj)
        else:
            return Block(obj)


class AbsBlock(GenericBlock[KT, CT], Generic[KT, VT, LT, CT], metaclass=ABCMeta):
    """Abstract class for SLHA blocks."""

    @abstractmethod
    def __init__(self, obj: Union[BlockHeadLine, str]) -> None:
        super().__init__()
        if isinstance(obj, BlockHeadLine):
            self.head = obj  # type: BlockHeadLine
        elif isinstance(obj, str):
            self.head = BlockHeadLine(name=obj)
        else:
            raise TypeError(obj)
        self._comment = CommentInterface(self)
        self._data = NotImplemented  # must be initialized in subclasses

    @property
    def name(self) -> str:
        """Return the name of block (always in upper case)."""
        return self.head.name

    @property
    def q(self) -> Optional[float]:
        """Return the Q value."""
        return self.head.q

    @q.setter
    def q(self, value: Optional[float]) -> None:
        self.head.q = value

    @abstractmethod
    def __getitem__(self, key: KT) -> Union[VT, Sequence[VT]]:
        """Return the value corresponding to the key."""

    @abstractmethod
    def __setitem__(self, key: KT, value: VT) -> None:
        """Set the value for the key."""

    @abstractmethod
    def __delitem__(self, key: KT) -> None:
        """Delete the value for the key."""

    @abstractmethod
    def update_line(self, line: LT) -> None:
        """Add the line to the block, overriding if exists."""

    @abstractmethod
    def keys(self, sort: bool = False) -> Iterator[KT]:
        """Return the keys."""

    __iter__ = keys

    @abstractmethod
    def items(self, sort: bool = False) -> Iterator[Tuple[KT, VT]]:
        """Return (key, value) tuples."""

    @abstractmethod
    def _lines(self, sort: bool = False) -> Iterator[Tuple[KT, LT]]:
        pass


class Block(AbsBlock[KeyType, ValueType, ValueLine, str]):
    """SLHA block that has one value for one key."""

    def __init__(self, obj: Union[BlockHeadLine, str]) -> None:
        super().__init__(obj)
        self._data = OrderedDict()  # type: OrderedDict[KeyType, ValueLine]

    def __getitem__(self, key: KeyType) -> ValueType:
        """Return the value corresponding to the key."""
        return self._data[key].value

    def __setitem__(self, key: KeyType, value: ValueType) -> None:
        """Set the value for the key."""
        if key in self._data:
            self._data[key].value = value
        else:
            self._data[key] = ValueLine.new(key, value)

    def __delitem__(self, key: KeyType) -> None:
        """Delete the value for the key."""
        del self._data[key]

    def update_line(self, line: ValueLine) -> None:
        """Add the line to the block, overriding if exists."""
        self._data[line.key] = line

    def merge(self, another: "Union[Block, InfoBlock]") -> None:
        """Merge another block."""
        if isinstance(another, Block):
            for _, line in another._lines():
                self.update_line(line)
        else:
            raise ValueError(another)

    def get(self, *key: Any, default: T) -> Union[ValueType, T]:
        """Return the value for the key if exists, or default value."""
        if key in self._data:
            return self.__getitem__(key)
        else:
            return default

    def keys(self, sort: bool = False) -> Iterator[KeyType]:
        """Return the keys."""
        for k, _ in self._lines(sort=sort):
            yield k

    __iter__ = keys

    def items(self, sort: bool = False) -> Iterator[Tuple[KeyType, ValueType]]:
        """Return (key, value) tuples."""
        for k, line in self._lines(sort=sort):
            yield k, line.value

    def _lines(self, sort: bool = False) -> Iterator[Tuple[KeyType, ValueLine]]:
        if sort:
            key_line_tuples = list(self._data.items())
            key_line_tuples.sort(key=lambda k: k[0])
            for i in key_line_tuples:
                yield i
        else:
            for i in self._data.items():
                yield i

    def _get_comment(self, key: KeyType) -> str:
        return self._data[key].comment

    def _get_pre_comment(self, key: KeyType) -> List[str]:
        return self._data[key].pre_comment

    def _set_comment(self, key: KeyType, value: Optional[str]) -> None:
        self._data[key].comment = value or ""

    def _set_pre_comment(self, key: KeyType, value: Optional[Sequence[str]]) -> None:
        self._data[key].pre_comment = [v for v in value] if value else []


class InfoBlock(AbsBlock[InfoKeyType, InfoValueType, InfoLine, List[str]]):
    """SLHA block that may have multiple values for one key."""

    def __init__(self, obj: Union[BlockHeadLine, str]) -> None:
        super().__init__(obj)
        self._data = []  # type: List[InfoLine]

    def __getitem__(self, key: InfoKeyType) -> Sequence[InfoValueType]:
        """Return the value corresponding to the key."""
        return tuple(line.value for line in self._data if line.key == key)

    def __setitem__(self, key: InfoKeyType, value: Sequence[InfoValueType]) -> None:
        """Set the value for the key."""
        if isinstance(value, str):
            raise TypeError(value)  # Fail-safe; only List[str] is allowed!
        self.__delitem__(key)
        self._data.extend([InfoLine(key, v) for v in value])

    def __delitem__(self, key: InfoKeyType) -> None:
        """Delete the value for the key."""
        self._data = [line for line in self._data if line.key != key]

    def update_line(self, line: InfoLine) -> None:
        """Add the line to the block, overriding if exists."""
        self.__delitem__(line.key)
        self._data.append(line)

    def append_line(self, line: InfoLine) -> None:
        """Add the line, appending to the existing one if exists."""
        self._data.append(line)

    def append(self, key: InfoKeyType, value: InfoValueType) -> None:
        """Append the value for the key."""
        self.append_line(InfoLine(key, value))

    def merge(self, another: "Union[Block, InfoBlock]") -> None:
        """Merge another block."""
        if isinstance(another, InfoBlock):
            updated = {}  # type: MutableMapping[InfoKeyType, bool]
            for key, line in another._lines():
                if updated.get(key):
                    self.append_line(line)
                else:
                    updated[key] = True
                    self.update_line(line)
        else:
            raise ValueError(another)

    def keys(self, sort: bool = False) -> Iterator[InfoKeyType]:
        """Return the keys."""
        keys_dict = {}  # type: MutableMapping[InfoKeyType, bool]
        for line in self._data:
            keys_dict[line.key] = True
        keys = list(keys_dict.keys())
        if sort:
            keys.sort()
        for k in keys:
            yield k

    __iter__ = keys

    def items(self, sort: bool = False) -> Iterator[Tuple[InfoKeyType, InfoValueType]]:
        """Return (key, value) tuples."""
        for key, line in self._lines(sort):
            yield key, line.value

    def _lines(self, sort: bool = False) -> Iterator[Tuple[InfoKeyType, InfoLine]]:
        for key in self.keys(sort):
            for line in self._data:
                if line.key == key:
                    yield key, line

    def _get_comment(self, key: InfoKeyType) -> List[str]:
        return [line.comment for line in self._data if line.key == key]

    def _get_pre_comment(self, key: InfoKeyType) -> List[str]:
        return self._data[key].pre_comment

    def _set_comment(self, key: InfoKeyType, value: Optional[Sequence[str]]) -> None:
        lines = [line for line in self._data if line.key == key]
        if value is None:
            value = []
        if len(lines) < len(value):
            raise ValueError(value)  # too many values
        for i, line in enumerate(lines):
            if i < len(value):
                line.comment = value[i]

    def _set_pre_comment(
        self, key: InfoKeyType, value: Optional[Sequence[str]]
    ) -> None:
        for line in self._data:
            if line.key == key:
                line.pre_comment = [v for v in value] if value else []
                value = []  # to remove all the remaining pre_comment


class Decay(GenericBlock[DecayKeyType, str]):
    """Decay block."""

    br_normalize_threshold = 1.0e-6  # type: ClassVar[float]

    def __init__(self, obj: Union[DecayHeadLine, int]) -> None:
        super().__init__()
        if isinstance(obj, DecayHeadLine):
            self.head = obj  # type: DecayHeadLine
        elif isinstance(obj, int):
            self.head = DecayHeadLine(pid=obj, width=0)
        else:
            raise TypeError(obj)
        self._data = (
            OrderedTupleOrderInsensitiveDict()
        )  # type: OrderedTupleOrderInsensitiveDict[DecayKeyType, DecayLine]

    @property
    def pid(self) -> int:
        """Return the pid of mother particle."""
        return self.head.pid

    @property
    def width(self) -> float:
        """Return the total width."""
        return self.head.width

    def update_line(self, line: DecayLine) -> None:
        """Add the line to the block, overriding if exists."""
        self._data[line.key] = line

    def br(self, *key: int) -> DecayValueType:
        """Return the BR of given channel."""
        if key in self._data:
            return self._data[key].br
        else:
            return 0

    def partial_width(self, *key: int) -> float:
        """Return the width of given channel."""
        return self.width * self.br(*key)

    def keys(self, sort: bool = False) -> Iterator[DecayKeyType]:
        """Return the keys."""
        for k, _ in self._lines(sort):
            yield k

    __iter__ = keys

    def items_br(self, sort=False):
        # type: (bool)->Iterator[Tuple[DecayKeyType, DecayValueType]]
        """Return (key, BR) tuples, sorted by the BR."""
        for k, line in self._lines(sort):
            yield k, line.br

    def items_partial_width(self, sort=False):
        # type: (bool)->Iterator[Tuple[DecayKeyType, float]]
        """Return (key, width) tuples, sorted by the BR."""
        for k, line in self._lines(sort):
            yield k, self.width * line.br

    def _lines(self, sort: bool = False) -> Iterator[Tuple[DecayKeyType, DecayLine]]:
        if sort:
            key_line_tuples = list(self._data.items())
            key_line_tuples.sort(key=lambda k: -k[1].br)
            for i in key_line_tuples:
                yield i
        else:
            for i in self._data.items():
                yield i

    def _get_comment(self, key: DecayKeyType) -> str:
        return self._data[key].comment

    def _get_pre_comment(self, key: DecayKeyType) -> List[str]:
        return self._data[key].pre_comment

    def _set_comment(self, key: DecayKeyType, value: Optional[str]) -> None:
        self._data[key].comment = value or ""

    def _set_pre_comment(
        self, key: DecayKeyType, value: Optional[Sequence[str]]
    ) -> None:
        self._data[key].pre_comment = [v for v in value] if value else []

    def normalize(self, force: bool = False) -> None:
        """Normalize the branching ratios.

        This method normalize all the branching ratios so that the sum becomes
        unity or less. In particular, if `force` is set True, they are
        normalized so that the sum becomes unity, regardless of the current
        value.

        If `force` is False and the sum is less than one, the branching ratio
        is not normalized, assuming that some decay channels are not listed. If
        `force` is False and the sum slightly exceeds the unity, the branching
        ratios are normalized, while if the excess is larger than
        `br_normalize_threshold`, `ValueError` is raised.
        """
        br_list = [br for _, br in self.items_br(sort=True)]
        total = sum(reversed(br_list))  # sum taken from smaller to reduce error

        if not total > 0:
            return  # stable particle
        elif force:
            logger.debug("BR for %d force normalized: %g", self.pid, total)
            pass  # to normalize
        elif total > 1 + self.br_normalize_threshold:
            logger.critical("BR for %d exceeds unity: %g", self.pid, total)
            raise ValueError(total)
        elif total >= 1:
            pass  # to normalize
        else:  # if force==False and total < 1
            rest = 1 - total
            assert rest > 0
            if rest > self.br_normalize_threshold:
                if hasattr(self, "_br_warned"):
                    pass
                else:
                    # warn only once
                    self._br_warned = True
                    logger.warning("BR for %d is less than unity by %g", self.pid, rest)
            return  # not normalize

        for v in self._data.values():
            v.br /= total

    def set_partial_width(self, *args: Union[int, float]) -> None:
        """Update the partial width and recalculate BRs of all channels."""
        if len(args) < 3 or not all(isinstance(i, int) for i in args[:-1]):
            raise KeyError(*args)
        key = cast(List[int], args[:-1])
        new_partial_width = float(args[-1])

        self.normalize()

        if key in self._data:
            old_partial_width = self.partial_width(*key)
        else:
            old_partial_width = 0
            self.update_line(DecayLine(br=0, channel=key))

        # update total width
        old_width = self.width
        new_width = new_partial_width - old_partial_width + old_width
        self.head.width = new_width

        # update the modified channel
        self._data[key].br = new_partial_width / new_width
        target = self._data[key]

        for line in self._data.values():
            if line != target:
                line.br *= old_width / new_width

    def remove(self, *key: int) -> None:
        """Remove the channel and recalculate BRs of all the other channels."""
        self.set_partial_width(*key, 0)
        del self._data[key]
