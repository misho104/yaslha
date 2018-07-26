from collections import OrderedDict, _OrderedDictItemsView
from typing import cast, Optional, Union, List, MutableMapping

import yaslha.line
from yaslha.line import KeyType, ValueType, ChannelType, CommentPositionType, CommentPosition
import yaslha.dumper
import yaslha.parser
import yaslha.exceptions as exceptions


class SLHA:
    def __init__(self):
        self.blocks = OrderedDict()
        self.decays = OrderedDict()
        self._tail_comment = list()   # type: List[CommentLine]

    def dump(self, dumper=None)->str:
        if dumper is None:
            dumper = yaslha.dumper.SLHADumper()
        return dumper.dump(self)

    @property
    def tail_comment(self)->List['yaslha.line.CommentLine']:
        return self._tail_comment

    @tail_comment.setter
    def tail_comment(self, value: Union[str, List[str], List[yaslha.line.CommentLine]])->None:
        if isinstance(value, str):
            value = [value]
        self._tail_comment = [v if isinstance(v, yaslha.line.CommentLine)
                              else yaslha.line.CommentLine(v)
                              for v in value]


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
            self._comment_lines = dict()   # type: MutableMapping[CommentPositionType, List[yaslha.line.CommentLine]]
        elif isinstance(name, Block):
            # copy constructor
            self.name = name.name
            self.q = name.q
            self.head_comment = name.head_comment
            self._data = OrderedDict(name._data)
            self._comment_lines = name._comment_lines
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

    def add_line_comment(self, position: 'CommentPositionType', value: Union[str, yaslha.line.CommentLine])->None:
        if position not in self._comment_lines:
            self._comment_lines[position] = list()
        self._comment_lines[position].append(value if isinstance(value, yaslha.line.CommentLine)
                                             else yaslha.line.CommentLine(value))

    def set_line_comment(self,
                         position: 'CommentPositionType',
                         value: Union[str, List[str], List[yaslha.line.CommentLine]])->None:
        if isinstance(value, str):
            value = [value]
        self._comment_lines[position] = [v if isinstance(v, yaslha.line.CommentLine)
                                         else yaslha.line.CommentLine(v)
                                         for v in value]

    def clear_line_comment(self, position: 'CommentPositionType')->None:
        if position in self._comment_lines:
            del self._comment_lines[position]

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

    def line_comment(self, position: 'CommentPositionType')->List[yaslha.line.CommentLine]:
        return self._comment_lines.get(position, [])

    def line_comment_keys(self)->List[CommentPositionType]:
        return [v for v in self._comment_lines.keys() if not isinstance(v, CommentPosition)]

    # accessor to line itself
    def head_line(self)->yaslha.line.BlockLine:
        return yaslha.line.BlockLine(name=self.name, q=self.q, comment=self.head_comment)

    def value_lines(self, with_comment_lines: bool=True)->MutableMapping[KeyType, List[yaslha.line.AbsLine]]:
        result = OrderedDict()   # type: OrderedDict[KeyType, List[yaslha.line.AbsLine]]
        dumped_line_comment = set()
        for key, value in self._data.items():
            result[key] = cast(List[yaslha.line.AbsLine], self.line_comment(key)) if with_comment_lines else []
            result[key].append(value)
            dumped_line_comment.add(key)

        if with_comment_lines:
            for orphan_key in set(self.line_comment_keys()) - dumped_line_comment:
                exceptions.OrphanCommentWarning(self.line_comment(orphan_key)).call()
        return result

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
        return _OrderedDictItemsView(OrderedDict((k, v.value) for k, v in self._data.items()))


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
            self._comment_lines = dict()   # type: MutableMapping[CommentPositionType, List[yaslha.line.CommentLine]]
        elif isinstance(pid, Decay):
            # copy constructor
            self.pid = pid.pid
            self._width = pid._width
            self.head_comment = pid.head_comment
            self._data = pid._data
            self._comment_lines = pid._comment_lines
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

    def add_line_comment(self, position: 'CommentPositionType', value: Union[str, yaslha.line.CommentLine])->None:
        if position not in self._comment_lines:
            self._comment_lines[position] = list()
        self._comment_lines[position].append(value if isinstance(value, yaslha.line.CommentLine)
                                             else yaslha.line.CommentLine(value))

    def set_line_comment(self,
                         position: 'CommentPositionType',
                         value: Union[str, List[str], List[yaslha.line.CommentLine]])->None:
        if isinstance(value, str):
            value = [value]
        self._comment_lines[position] = [v if isinstance(v, yaslha.line.CommentLine)
                                         else yaslha.line.CommentLine(v)
                                         for v in value]

    def clear_line_comment(self, position: 'CommentPositionType')->None:
        if position in self._comment_lines:
            del self._comment_lines[position]

    # getter
    def __getitem__(self, channel: ChannelType)->float:
        return self._data[channel].width / self.width

    def get_br(self, channel: ChannelType)->float:
        if channel in self._data:
            # TODO: write a good method to chop after 1+8 digits
            return float('{:.10g}'.format(self._data[channel].width / self.width))
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

    def line_comment(self, position: 'CommentPositionType')->List[yaslha.line.CommentLine]:
        return self._comment_lines.get(position, [])

    def line_comment_keys(self)->List[CommentPositionType]:
        return [v for v in self._comment_lines.keys() if not isinstance(v, CommentPosition)]

    # accessor to line itself
    def head_line(self)->yaslha.line.DecayBlockLine:
        return yaslha.line.DecayBlockLine(pid=self.pid, width=self.width, comment=self.head_comment)

    def value_lines(self, with_comment_lines: bool=True)->MutableMapping[KeyType, List[yaslha.line.AbsLine]]:
        result = OrderedDict()   # type: OrderedDict[KeyType, List[yaslha.line.AbsLine]]
        dumped_line_comment = set()
        for ch, value in self._data.items():
            result[ch] = cast(List[yaslha.line.AbsLine], self.line_comment(ch)) if with_comment_lines else []
            result[ch].append(yaslha.line.DecayLine(br=self.get_br(ch), channel=ch, comment=self.comment(ch)))
            dumped_line_comment.add(ch)

        if with_comment_lines:
            for orphan_key in set(self.line_comment_keys()) - dumped_line_comment:
                exceptions.OrphanCommentWarning(self.line_comment(orphan_key)).call()
        return result

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
        return _OrderedDictItemsView(OrderedDict((k, v.width) for k, v in self._data.items()))

    def rename_channel(self, old: ChannelType, new: ChannelType):
        if old not in self or (new != old and new in self):
            raise KeyError

        old_br = self[old]
        old_comment = self.comment(old) or ''
        old_line_comment = self.line_comment(old)

        del self._data[old]
        self.clear_line_comment(old)

        self[new] = old_br
        self.set_comment(new, old_comment)
        if old_line_comment:  # not do if it is empty
            self.set_line_comment(new, old_line_comment)
