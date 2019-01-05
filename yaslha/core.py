from collections import OrderedDict
import copy
from typing import cast, Tuple, Optional, Union, List, MutableMapping, Sequence, KeysView  # noqa: F401

import yaslha.dumper
import yaslha.exceptions as exceptions
import yaslha.line
import yaslha.parser
from yaslha.line import CommentPositionType, CommentPosition  # noqa: F401
from yaslha.utility import KeyType, ValueType, ChannelType    # noqa: F401


class SLHA:
    def __init__(self, obj=None):
        # type: (Optional[SLHA])->None
        if isinstance(obj, SLHA):
            # copy constructor
            self.blocks = copy.deepcopy(obj.blocks)                # type: OrderedDict[str, Block]
            self.decays = copy.deepcopy(obj.decays)                # type: OrderedDict[int, Decay]
            self._tail_comment = copy.deepcopy(obj._tail_comment)  # type: List[yaslha.line.CommentLine]
        else:
            self.blocks = OrderedDict()
            self.decays = OrderedDict()
            self._tail_comment = list()

    def dump(self, dumper=None):
        # type: (Optional[yaslha.dumper.AbsDumper])->str
        if dumper is None:
            dumper = yaslha.dumper.SLHADumper()
        return dumper.dump(self)

    @property
    def tail_comment(self):
        # type: ()->List[yaslha.line.CommentLine]
        return self._tail_comment

    @tail_comment.setter
    def tail_comment(self, value):
        # type: (Union[str, List[str], List[yaslha.line.CommentLine]])->None
        if isinstance(value, str):
            value = [value]
        self._tail_comment = [v if isinstance(v, yaslha.line.CommentLine)
                              else yaslha.line.CommentLine(v)
                              for v in value]

    def __getitem__(self, block_name_or_decay_pid):
        # type: (Union[str, int])->Union[Block, Decay]
        if isinstance(block_name_or_decay_pid, str):
            name = block_name_or_decay_pid.upper()
            return self.blocks[name]
        elif isinstance(block_name_or_decay_pid, int):
            return self.decays[block_name_or_decay_pid]
        else:
            raise TypeError

    def get(self, block_name, key=None, default=None):
        # type: (str, KeyType, Optional[ValueType])->Optional[ValueType]
        block_name = block_name.upper()
        if block_name in self.blocks:
            return self.blocks[block_name].get(key, default=default)
        else:
            return default

    def set(self, block_name, key, value, comment=''):
        # type: (str, KeyType, ValueType, str)->None
        block_name = block_name.upper()
        if block_name not in self.blocks:
            self.blocks[block_name] = Block(block_name)
        self.blocks[block_name].set(key, value, comment)

    def set_info(self, block_name, key, value, comment=''):
        # type: (str, int, Union[ValueType, List[ValueType]], Union[str, List[str]])->None
        block_name = block_name.upper()
        if block_name not in self.blocks:
            self.blocks[block_name] = Block(block_name)
        value = [str(v) for v in value] if isinstance(value, list) else str(value)
        self.blocks[block_name][key] = yaslha.line.InfoLine(key, value, comment)

    def append_info(self, block_name, key, value, comment=''):
        # type: (str, int, ValueType, str)->None
        block_name = block_name.upper()
        obj = self.blocks.get(block_name, key)
        if not isinstance(obj, yaslha.line.InfoLine):
            raise TypeError('{}-{} is not InfoLine.'.format(block_name, key))
        obj.append(str(value), comment)

    def br(self, mother, *daughters):
        # type: (int, int)->Optional[float]
        # TODO: we will have a 'NormalizedOrderedDict' to handle with order- (as well as case-) insensitive dict.
        try:
            decay = self.decays[mother]
        except KeyError:
            return None
        d = sorted(daughters)

        for k, v in decay.items_br():
            if sorted(k) == d:
                return v
        return 0

    def merge(self, another):
        # type: (SLHA)->None
        for k, v in another.blocks.items():
            if k in self.blocks:
                self.blocks[k].merge(v)
            else:
                self.blocks[k] = copy.deepcopy(v)
        self.decays.update(copy.deepcopy(another.decays))
        if another._tail_comment:
            self._tail_comment = copy.deepcopy(another._tail_comment)


class Block:
    """Represent a block.

    Block._data is an OrderedDict, whose values are a Line object. Usual
    accessor should access the value of Line, while comment accessors
    can access its comment.
    """

    def __init__(self, name, q=None, head_comment=''):
        # type: (Union[str, 'Block'], Optional[float], str)->None
        if isinstance(name, str):
            # normal constructor
            self.name = name                  # type: str
            self.q = q                        # type: Optional[float]
            # comment in BLOCK line
            self.head_comment = head_comment  # type: str
            self._data = OrderedDict()        # type: OrderedDict[KeyType, yaslha.line.AbsLine]
            self._comment_lines = dict()      # type: MutableMapping[CommentPositionType, List[yaslha.line.CommentLine]]
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
        # type: ()->str
        return self._name

    @name.setter
    def name(self, new_name):
        # type: (str)->None
        self._name = new_name.upper()

    # setter
    def __setitem__(self, key, obj):
        # type: (KeyType, Union[ValueType, yaslha.line.AbsLine])->None
        if isinstance(obj, yaslha.line.AbsLine):
            self._data[key] = obj
        else:
            self._data[key] = yaslha.line.ValueLine(key, obj)

    def set_comment(self, key, comment):
        # type: (KeyType, str)->None
        if key in self._data:
            self._data[key].comment = comment
        else:
            raise KeyError  # developer level error; user won't see this.

    def set(self, key, value, comment=''):
        # type: (KeyType, ValueType, str)->None
        self.__setitem__(key, yaslha.line.ValueLine(key, value, comment))

    def add_line_comment(self, position, value):
        # type: (CommentPositionType, Union[str, yaslha.line.CommentLine])->None
        if position not in self._comment_lines:
            self._comment_lines[position] = list()
        self._comment_lines[position].append(value if isinstance(value, yaslha.line.CommentLine)
                                             else yaslha.line.CommentLine(value))

    def set_line_comment(self, position, value):
        # type: (CommentPositionType, Union[str, List[str], List[yaslha.line.CommentLine]])->None
        if isinstance(value, str):
            value = [value]
        self._comment_lines[position] = [v if isinstance(v, yaslha.line.CommentLine)
                                         else yaslha.line.CommentLine(v)
                                         for v in value]

    def clear_line_comment(self, position):
        # type: (CommentPositionType)->None
        if position in self._comment_lines:
            del self._comment_lines[position]

    # getter
    def __getitem__(self, key=None):
        # type: (KeyType)->ValueType
        return self._data[key].value

    def get(self, key=None, default=None):
        # type: (KeyType, Optional[ValueType])->Optional[ValueType]
        if key in self._data:
            return self._data[key].value
        else:
            return default

    def get_line_obj(self, key=None, default=None):
        # type: (KeyType, Optional[yaslha.line.AbsLine])->Optional[yaslha.line.AbsLine]
        if key in self._data:
            return self._data[key]
        else:
            return default

    def comment(self, key=None, default=''):
        # type: (KeyType, str)->Union[str, List[str]]
        if key in self._data or default is None:
            return self._data[key].comment
        else:
            return default

    def line_comment(self, position):
        # type: (CommentPositionType)->List[yaslha.line.CommentLine]
        return self._comment_lines.get(position, [])

    def line_comment_keys(self):
        # type: ()->List[CommentPositionType]
        return [v for v in self._comment_lines.keys() if not isinstance(v, CommentPosition)]

    # accessor to line itself
    def head_line(self):
        # type: ()->yaslha.line.BlockLine
        return yaslha.line.BlockLine(name=self.name, q=self.q, comment=self.head_comment)

    def value_lines(self, with_comment_lines=True):
        # type: (bool)->MutableMapping[KeyType, List[yaslha.line.AbsLine]]
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
    def __delitem__(self, key):
        # type: (KeyType)->None
        self._data.__delitem__(key)

    def __contains__(self, key):
        # type: (KeyType)->bool
        return self._data.__contains__(key)

    def __len__(self):
        # type: ()->int
        return self._data.__len__()

    def keys(self):
        # type: ()->KeysView[KeyType]
        return self._data.keys()

    def items(self):
        # type: ()->List[Tuple[KeyType, ValueType]]
        return [(k, v.value) for k, v in self._data.items()]

    def merge(self, another):
        # type: (Block)->None
        self.q = another.q
        if another.head_comment:
            self.head_comment = copy.deepcopy(another.head_comment)
        self._data.update(copy.deepcopy(another._data))
        self._comment_lines.update(copy.deepcopy(another._comment_lines))


class PartialWidth:
    def __init__(self, width, comment=''):
        # type: (float, str)->None
        self.width = width      # type: float
        self.comment = comment  # type: str


class Decay:
    def __init__(self, pid, width=0., head_comment=''):
        # type: (Union[int, Decay], float, str)->None
        if isinstance(pid, int):
            # normal constructor
            self.pid = pid                    # type: int
            self._width = width               # type: float
            self.head_comment = head_comment  # type: str
            self._data = OrderedDict()        # type: OrderedDict[ChannelType, PartialWidth]
            self._comment_lines = dict()      # type: MutableMapping[CommentPositionType, List[yaslha.line.CommentLine]]
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
    def width(self):
        # type: ()->float
        return self._width   # forbid direct set of width

    def _update_width(self):
        # type: ()->float
        self._width = sum(self.values())
        return self._width

    # setter
    def __setitem__(self, channel, br):
        # type: (ChannelType, Union[float, yaslha.line.DecayLine])->None
        if isinstance(br, yaslha.line.DecayLine):
            self._data[channel] = PartialWidth(self.width * br.value, br.comment)
        else:
            self._data[channel] = PartialWidth(self.width * br, '')

    def set_partial_width(self, channel, width, comment=''):
        # type: (ChannelType, float, str)->None
        if channel in self._data:
            self._data[channel].width = width
            if comment is not None:
                self._data[channel].comment = comment
        else:
            self._data[channel] = PartialWidth(width, comment)
        self._update_width()

    def set_comment(self, channel, comment):
        # type: (ChannelType, str)->None
        if channel in self._data:
            self._data[channel].comment = comment
        else:
            raise KeyError  # developer level error; user won't see this.

    def add_line_comment(self, position, value):
        # type: (CommentPositionType, Union[str, yaslha.line.CommentLine])->None
        if position not in self._comment_lines:
            self._comment_lines[position] = list()
        self._comment_lines[position].append(value if isinstance(value, yaslha.line.CommentLine)
                                             else yaslha.line.CommentLine(value))

    def set_line_comment(self, position, value):
        # type: (CommentPositionType, Union[str, List[str], List[yaslha.line.CommentLine]])->None
        if isinstance(value, str):
            value = [value]
        self._comment_lines[position] = [v if isinstance(v, yaslha.line.CommentLine)
                                         else yaslha.line.CommentLine(v)
                                         for v in value]

    def clear_line_comment(self, position):
        # type: (CommentPositionType)->None
        if position in self._comment_lines:
            del self._comment_lines[position]

    # getter
    def br(self, channel):
        # type: (ChannelType)->float
        if channel in self._data:
            # TODO: write a good method to chop after 1+8 digits
            return float('{:.10g}'.format(self._data[channel].width / self.width))
        else:
            return 0.0

    def partial_width(self, channel):
        # type: (ChannelType)->float
        if channel in self._data:
            return self._data[channel].width
        else:
            return 0.0

    def comment(self, channel, default=''):
        # type: (ChannelType, str)->str
        if channel in self._data or default is None:
            return self._data[channel].comment
        else:
            return default

    def line_comment(self, position):
        # type: (CommentPositionType)->List[yaslha.line.CommentLine]
        return self._comment_lines.get(position, [])

    def line_comment_keys(self):
        # type: ()->List[CommentPositionType]
        return [v for v in self._comment_lines.keys() if not isinstance(v, CommentPosition)]

    # accessor to line itself
    def head_line(self):
        # type: ()->yaslha.line.DecayBlockLine
        return yaslha.line.DecayBlockLine(pid=self.pid, width=self.width, comment=self.head_comment)

    def value_lines(self, with_comment_lines=True):
        # type: (bool)->MutableMapping[KeyType, List[yaslha.line.AbsLine]]
        result = OrderedDict()   # type: OrderedDict[KeyType, List[yaslha.line.AbsLine]]
        dumped_line_comment = set()
        for ch, value in self._data.items():
            result[ch] = cast(List[yaslha.line.AbsLine], self.line_comment(ch)) if with_comment_lines else []
            result[ch].append(yaslha.line.DecayLine(br=self.br(ch), channel=ch, comment=self.comment(ch)))
            dumped_line_comment.add(ch)

        if with_comment_lines:
            for orphan_key in set(self.line_comment_keys()) - dumped_line_comment:
                exceptions.OrphanCommentWarning(self.line_comment(orphan_key)).call()
        return result

    # other accessors
    def __delitem__(self, channel):
        # type: (ChannelType)->None
        self._data.__delitem__(channel)
        self._update_width()

    def __contains__(self, channel):
        # type: (ChannelType)->bool
        return self._data.__contains__(channel)

    def __len__(self):
        # type: ()->int
        return self._data.__len__()

    def keys(self):
        # type: ()->KeysView[ChannelType]
        return self._data.keys()

    def values(self):
        # type: ()->List[float]
        return [v.width for v in self._data.values()]

    def items_width(self):
        # type: ()->List[Tuple[ChannelType, float]]
        return [(k, v.width) for k, v in self._data.items()]

    def items_br(self):
        # type: ()->List[Tuple[ChannelType, float]]
        return [(k, v.width / self.width) for k, v in self._data.items()]

    def rename_channel(self, old, new):
        # type: (ChannelType, ChannelType)->None
        if old not in self or (new != old and new in self):
            raise KeyError

        old_br = self.br(old)
        old_comment = self.comment(old) or ''
        old_line_comment = self.line_comment(old)

        del self._data[old]
        self.clear_line_comment(old)

        self[new] = old_br
        self.set_comment(new, old_comment)
        if old_line_comment:  # not do if it is empty
            self.set_line_comment(new, old_line_comment)
