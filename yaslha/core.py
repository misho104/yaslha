from collections import OrderedDict, _OrderedDictItemsView
from typing import cast, Optional, Union, Tuple, List, Sequence  # noqa: F401

import yaslha.line
from yaslha.line import KeyType, ValueType, ChannelType
import yaslha.dumper
import yaslha.parser


class SLHA:
    def __init__(self):
        self.blocks = OrderedDict()
        self.decays = OrderedDict()

    def dump(self, dumper=None)->str:
        if dumper is None:
            dumper = yaslha.dumper.SLHADumper()
        return dumper.dump(self)


class Block:
    """Represent a block.

    Block._data is an OrderedDict, whose values are a Line object. Usual
    accessor should access the value of Line, while comment accessors
    can access its comment.
    """

    def __init__(self, name: Union[str, 'Block'], q: Optional[float] = None, head_comment: str='')->None:
        if isinstance(name, str):
            # normal constructor
            self.name = name
            self.q = q
            self.head_comment = head_comment      # comment in BLOCK line
            self._data = OrderedDict()  # type: OrderedDict[KeyType, yaslha.line.AbsLine]
        elif isinstance(name, Block):
            # copy constructor
            self.name = name.name
            self.q = name.q
            self.head_comment = name.head_comment
            self._data = OrderedDict(name._data)
        else:
            raise TypeError  # developer level error; user won't see this.

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name.upper()

    # setter
    def __setitem__(self, key: KeyType, obj: Union[ValueType, yaslha.line.AbsLine])->None:
        if isinstance(obj, yaslha.line.AbsLine):
            self._data[key] = obj
        else:
            self._data[key] = yaslha.line.ValueLine(key, obj)

    def set_comment(self, key: KeyType, comment: str)->None:
        if key in self._data:
            self._data[key].comment = comment
        else:
            raise KeyError  # developer level error; user won't see this.

    def set(self, key: KeyType, value: ValueType, comment: str=''):
        self.__setitem__(key, yaslha.line.ValueLine(key, value, comment))

    # getter
    def __getitem__(self, key: KeyType)->ValueType:
        return self._data[key].value

    def get(self, key: KeyType, default=None):
        if key in self._data:
            return self._data[key].value
        else:
            return default

    def get_line_obj(self, key: KeyType, default=None):
        if key in self._data:
            return self._data[key]
        else:
            return default

    def comment(self, key: KeyType, default: Optional[str]=None):
        if key in self._data or default is None:
            return self._data[key].comment
        else:
            return default

    # accessor to line itself
    def head_line(self)->yaslha.line.BlockLine:
        return yaslha.line.BlockLine(name=self.name, q=self.q, comment=self.head_comment)

    def value_lines(self)->List[yaslha.line.AbsLine]:
        return list(self._data.values())

    def lines(self)->List[yaslha.line.AbsLine]:
        head = cast(yaslha.line.AbsLine, self.head_line())
        body = cast(List[yaslha.line.AbsLine], self.value_lines())
        return [head] + body

    # other accessors
    def __delitem__(self, key)->None:
        self._data.__delitem__(key)

    def __contains__(self, key: KeyType)->bool:
        return self._data.__contains__(key)

    def __len__(self):
        return self._data.__len__()

    def keys(self):
        return self._data.keys()

    def items(self):
        return _OrderedDictItemsView([(k, v.value) for k, v in self._data.items()])


class PartialWidth:
    def __init__(self, width: float, comment: str ='')->None:
        self.width = width
        self.comment = comment


class Decay:
    def __init__(self, pid: Union[int, 'Decay'], width: Optional[float]=None, head_comment: str='')->None:
        if isinstance(pid, int):
            # normal constructor
            self.pid = pid              # type: int
            self._width = width          # type: float
            self.head_comment = head_comment
            self._data = OrderedDict()  # type: OrderedDict[ChannelType, PartialWidth]
        elif isinstance(pid, Decay):
            # copy constructor
            self.pid = pid.pid
            self._width = pid._width
            self.head_comment = pid.head_comment
            self._data = OrderedDict(pid._data)
        else:
            raise TypeError  # developer level error; user won't see this.

    @property
    def width(self)->float:
        return self._width   # forbid direct set of width

    def _update_width(self)->float:
        self._width = sum(self.values())
        return self._width

    # setter
    def __setitem__(self, channel: ChannelType, br: Union[float, yaslha.line.DecayLine])->None:
        if isinstance(br, yaslha.line.DecayLine):
            self._data[channel] = PartialWidth(self.width * br.value, br.comment)
        else:
            self._data[channel] = PartialWidth(self.width * br, '')

    def set_partial_width(self, channel: ChannelType, width: float, comment: Optional[str] = None):
        if channel in self._data:
            self._data[channel].width = width
            if comment is not None:
                self._data[channel].comment = comment
        else:
            self._data[channel] = PartialWidth(width, comment or '')
        self._update_width()

    def set_comment(self, channel: ChannelType, comment: str):
        if channel in self._data:
            self._data[channel].comment = comment
        else:
            raise KeyError  # developer level error; user won't see this.

    # getter
    def __getitem__(self, channel: ChannelType)->float:
        return self._data[channel].width / self.width

    def get_br(self, channel: ChannelType)->float:
        if channel in self._data:
            return float(f'{self._data[channel].width / self.width:.10g}')
        else:
            return 0.0

    def get_partial_width(self, channel: ChannelType)->float:
        if channel in self._data:
            return self._data[channel].width
        else:
            return 0.0

    def comment(self, channel: ChannelType, default: Optional[str]=None):
        if channel in self._data or default is None:
            return self._data[channel].comment
        else:
            return default

    # accessor to line itself
    def head_line(self)->yaslha.line.DecayBlockLine:
        return yaslha.line.DecayBlockLine(pid=self.pid, width=self.width, comment=self.head_comment)

    def value_lines(self)->List[yaslha.line.AbsLine]:
        return [yaslha.line.DecayLine(br=self.get_br(ch), channel=ch, comment=self.comment(ch))
                for ch in self.keys()]

    def lines(self)->List[yaslha.line.AbsLine]:
        head = cast(yaslha.line.AbsLine, self.head_line())
        body = cast(List[yaslha.line.AbsLine], self.value_lines())
        return [head] + body

    # other accessors
    def __delitem__(self, channel):
        self._data.__delitem__(channel)
        self.update_width()

    def __contains__(self, channel: ChannelType)->bool:
        return self._data.__contains__(channel)

    def __len__(self):
        return self._data.__len__()

    def keys(self):
        return self._data.keys()

    def values(self):
        return [v.width for v in self._data.values()]

    def items(self):
        return _OrderedDictItemsView([(k, v.value) for k, v in self._data.items()])
