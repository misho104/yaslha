"""Module of SLHA object class."""
import copy
import logging
from collections import OrderedDict
from typing import Any, List, Tuple, TypeVar, Union

from yaslha._collections import OrderedCaseInsensitiveDict as CIDict
from yaslha.block import AbsBlock, Block, Decay, InfoBlock
from yaslha.line import BlockHeadLine, DecayValueType, InfoLine, ValueLine, ValueType

BlockValueLine = Union[ValueLine, InfoLine]
SLHAItemValueType = Union[Block, Decay, ValueType, DecayValueType]
T = TypeVar("T")
logger = logging.getLogger(__name__)


class SLHA:
    """SLHA object, representing a SLHA-format text."""

    def __init__(self) -> None:
        self.blocks = CIDict()  # type: CIDict[str, Union[Block, InfoBlock]]
        self.decays = OrderedDict()  # type: OrderedDict[int, Decay]
        self.tail_comment = []  # type: List[str]

    def add_block(self, obj: Union["Block", "InfoBlock", "Decay"]) -> None:
        """Add a block to SLHA file.

        The name is automatically detected from the object.
        """
        if isinstance(obj, AbsBlock):
            self.blocks[obj.name] = obj
        elif isinstance(obj, Decay):
            self.decays[obj.pid] = obj
        else:
            raise TypeError

    @staticmethod
    def _key_reduce(key: Any) -> Tuple[Union[str, int], Any]:
        if isinstance(key, str) or isinstance(key, int):
            return key, None
        elif len(key) == 1:
            return key[0], None
        elif isinstance(key[0], str):
            return key[0], (key[1] if len(key) == 2 else key[1:])
        else:
            # decay block does not allow deep indexing
            raise KeyError(key)

    def __getitem__(self, key: Any) -> Any:
        """Get values of SLHA object or deeper.

        ``SLHA[str]`` and ``SLHA[int]`` give the specified block and decay
        block, respectively. For ordinary blocks, further referencing is
        possible as ``SLHA[str, *key]``, while decay blocks refuse such
        referencing for safety.
        """
        if isinstance(key, str):
            return self.blocks[key]
        elif isinstance(key, int):
            return self.decays[key]
        elif hasattr(key, "__len__") and len(key) >= 2 and isinstance(key[0], str):
            block = self.blocks[key[0]]
            return block[key[1] if len(key) == 2 else tuple(key[1:])]
        else:
            raise KeyError(key)

    def get(self, *key: Any, default: Any = None) -> Any:
        """Return the value if exists, or default."""
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set a value of SLHA object or deeper."""
        if isinstance(key, str):
            assert isinstance(value, Block) or isinstance(value, InfoBlock)
            value.head.name = key  # correct the name of Block
            self.blocks[key] = value
        elif isinstance(key, int):
            assert isinstance(value, Decay)
            value.head.pid = key  # correct the pid of Decay
            self.decays[key] = value
        elif hasattr(key, "__len__") and len(key) >= 2 and isinstance(key[0], str):
            if key[0] not in self.blocks:
                self.add_block(AbsBlock.new(BlockHeadLine(name=key[0])))
            block = self.blocks[key[0]]
            block[key[1] if len(key) == 2 else tuple(key[1:])] = value
        else:
            raise KeyError(key)

    def __delitem__(self, key: Any) -> None:
        """Delete values of SLHA object or deeper."""
        if isinstance(key, str):
            del self.blocks[key]
        elif isinstance(key, int):
            del self.decays[key]
        elif hasattr(key, "__len__") and len(key) >= 2 and isinstance(key[0], str):
            block = self.blocks[key[0]]
            del block[key[1] if len(key) == 2 else tuple(key[1:])]
        else:
            raise KeyError(key)

    def normalize(self, blocks: bool = True, decays: bool = True) -> None:
        """Normalize the head-lines so that names/pids match the dict keys."""
        if blocks:
            for name, b in self.blocks.items():
                b.head.name = name
        if decays:
            for pid, d in self.decays.items():
                d.head.pid = pid

    def merge(self, another: "SLHA") -> None:
        """Merge another SLHA data into this object."""
        for name, block in another.blocks.items():
            self_block = self.blocks.get(name)
            if self_block:
                self_block.merge(block)
            else:
                self.blocks[name] = copy.deepcopy(block)
        self.decays.update(copy.deepcopy(another.decays))
        if another.tail_comment:
            self.tail_comment = copy.deepcopy(another.tail_comment)
