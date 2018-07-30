from collections import OrderedDict
import enum
import json
import re
from typing import cast, Optional, MutableMapping, Any, Tuple, Mapping, List, Union  # noqa: F401

import ruamel.yaml

import yaslha
import yaslha.exceptions as exceptions
import yaslha.line
import yaslha.utility
from yaslha.line import CommentPosition
from yaslha.utility import _float, _clean, _flatten, KeyType


class BlocksOrder(enum.Enum):
    DEFAULT = 0
    KEEP = 1
    ABC = 2


class ValuesOrder(enum.Enum):
    DEFAULT = 0
    KEEP = 1
    SORTED = 2


class CommentsPreserve(enum.Enum):
    NONE = 0
    TAIL = 1
    ALL = 2

    def keep_line(self) -> bool:
        return self == CommentsPreserve.ALL

    def keep_tail(self) -> bool:
        return self != CommentsPreserve.NONE


class AbsDumper:
    def __init__(self,
                 blocks_order: Optional[BlocksOrder]=None,
                 values_order: Optional[ValuesOrder]=None,
                 comments_preserve: Optional[CommentsPreserve] = None,
                 )->None:

        config = yaslha.cfg['yaslha.dumper.AbsDumper']

        self.blocks_order = config.value('blocks_order', blocks_order, typ=BlocksOrder)
        self.values_order = config.value('values_order', values_order, typ=ValuesOrder)
        self.comments_preserve = config.value('comments_preserve', comments_preserve, typ=CommentsPreserve)

    def dump(self, block: 'yaslha.SLHA')->str:
        return NotImplemented

    def _blocks_sorted(self, slha: 'yaslha.SLHA')->List['yaslha.Block']:
        if self.blocks_order == BlocksOrder.KEEP:
            return list(slha.blocks.values())
        block_names = list(slha.blocks.keys())
        if self.blocks_order == BlocksOrder.ABC:
            block_names.sort()
        else:
            block_names = yaslha.utility.sort_blocks_default(block_names)
        return [slha.blocks[name] for name in block_names]

    def _decays_sorted(self, slha: 'yaslha.SLHA')->List['yaslha.Decay']:
        if self.values_order == ValuesOrder.KEEP:
            return list(slha.decays.values())
        pids = list(slha.decays.keys())
        if self.values_order == ValuesOrder.SORTED:
            pids.sort()
        else:
            pids = yaslha.utility.sort_pids_default(pids)
        return [slha.decays[pid] for pid in pids]

    def _block_lines_with_key_order(self, block: 'yaslha.Block')->Tuple[List[yaslha.line.AbsLine], List[KeyType]]:
        value_lines = block.value_lines(with_comment_lines=self.comments_preserve.keep_line())

        keys = list(value_lines.keys())
        if self.values_order == ValuesOrder.DEFAULT and block.name == 'MASS':
            keys_ = yaslha.utility.sort_pids_default(keys)  # to suppress strange mypy complaint
            keys = keys_
        elif self.values_order != ValuesOrder.KEEP:
            keys.sort()
        lines = _flatten([cast(yaslha.line.AbsLine, value_lines[key]) for key in keys])
        return lines, keys

    def _decay_lines_with_key_order(self, decay: 'yaslha.Decay')->Tuple[List[yaslha.line.AbsLine], List[KeyType]]:
        if self.values_order == ValuesOrder.DEFAULT:
            sorted_decay = yaslha.utility.copy_sorted_decay_block(decay, sort_by_br=True)
        elif self.values_order == ValuesOrder.SORTED:
            sorted_decay = yaslha.utility.copy_sorted_decay_block(decay, sort_by_br=False)
        else:
            sorted_decay = decay
        lines = _flatten(list(sorted_decay.value_lines(with_comment_lines=self.comments_preserve.keep_line()).values()))
        return lines, list(sorted_decay.keys())


class SLHADumper(AbsDumper):
    TAIL_COMMENTS_RE = re.compile('\#.*')

    @staticmethod
    def comment_out(line: str)->str:
        if not line:
            return '#'
        elif line.startswith(' '):
            return line.replace(' ', '#', 1)
        else:
            return '#' + line.replace('  ', ' ', 1)

    def __init__(self,
                 separate_blocks: Optional[bool]=None,
                 forbid_last_linebreak: Optional[bool]=None,
                 document_blocks: Optional[List[Union[int, str]]]=None,
                 **kwargs)->None:
        super().__init__(**kwargs)

        config = yaslha.cfg['yaslha.dumper.SLHADumper']

        self.separate_blocks = config.value('separate_blocks', separate_blocks, typ=bool)
        self.forbid_last_linebreak = config.value('forbid_last_linebreak', forbid_last_linebreak, typ=bool)
        self.document_blocks = [name.upper() if isinstance(name, str) else name for name
                                in config.value('document_blocks', document_blocks)]  # type: List[Union[int, str]]

        # hidden options
        self.block_str = config.value('block_str')
        self.decay_str = config.value('decay_str')
        self.float_lower = config.value('float_lower', typ=bool)
        self.write_version = config.value('write_version', typ=bool)

    def _e_float(self, v: float)->str:
        return ('{:16.8e}' if self.float_lower else '{:16.8E}').format(_float(v))

    def dump(self, slha: 'yaslha.SLHA')->str:
        blocks = [self.dump_block(block, document_block=(block.name in self.document_blocks))
                  for block in self._blocks_sorted(slha)]
        decays = [self.dump_decay(decay, document_block=(decay.pid in self.document_blocks))
                  for decay in self._decays_sorted(slha)]
        if self.comments_preserve.keep_line():
            tail_comment = [v.line for v in slha.tail_comment]
        else:
            tail_comment = []

        # configuration-depending operations
        blocks = blocks + decays
        if self.separate_blocks:
            for i in range(len(blocks)):
                if i > 0 and not blocks[i].startswith('#\n'):
                    blocks[i] = '#\n' + blocks[i]
            if not tail_comment or tail_comment[-1] != '#':
                tail_comment.append('#')

        version_string_old = '# written by {}'.format(yaslha.__pkgname__)
        version_string_new = '# written by {} {}\n'.format(yaslha.__pkgname__, yaslha.__version__)
        for i in range(len(blocks)):
            if blocks[i].startswith(version_string_old):
                blocks[i] = version_string_new if self.write_version else ''
                version_string_new = None
                break
        if self.write_version and version_string_new:
            blocks.insert(0, version_string_new)

        result = ''.join(blocks) + '\n'.join(tail_comment) + '\n'

        if self.forbid_last_linebreak:
            result = result.rstrip()

        return result

    def dump_block(self, block: 'yaslha.Block', document_block: bool=False)->str:
        head = [block.head_line()]  # type: List[yaslha.line.AbsLine]
        body, key_order = self._block_lines_with_key_order(block)
        tail = []                   # type: List[yaslha.line.AbsLine]
        if self.comments_preserve.keep_line():
            pre_comment = cast(List[yaslha.line.AbsLine], block.line_comment(CommentPosition.Prefix))
            head_comment = cast(List[yaslha.line.AbsLine], block.line_comment(CommentPosition.Heading))
            head = pre_comment + head + head_comment
            tail = cast(List[yaslha.line.AbsLine], block.line_comment(CommentPosition.Suffix))

        lines = _clean([self.dump_line(obj, block_name=block.name) for obj in head + body + tail])
        if document_block:
            lines = [self.comment_out(line) for line in lines]
        return '\n'.join(lines) + '\n'

    def dump_line(self, obj: yaslha.line.AbsLine, block_name: Optional[str]=None):
        # TODO: rewrite using singledispatcher
        if isinstance(obj, yaslha.line.CommentLine):
            if self.comments_preserve.keep_line():
                return self.dump_comment_line(obj)
            else:
                return ''
        if isinstance(obj, yaslha.line.BlockLine):
            line = self.dump_block_line(obj)
        elif isinstance(obj, yaslha.line.DecayBlockLine):
            line = self.dump_decayblock_line(obj)
        elif isinstance(obj, yaslha.line.DecayLine):
            line = self.dump_decay_line(obj)
        elif isinstance(obj, yaslha.line.InfoLine):
            line = self.dump_info_line(obj, block_name)
        elif isinstance(obj, yaslha.line.ValueLine):
            line = self.dump_value_line(obj, block_name)
        else:
            exceptions.UnrecognizedLineObjectWarning(obj).call()
            return ''

        if self.comments_preserve.keep_tail():
            return line
        else:
            return self.TAIL_COMMENTS_RE.sub('#', line)

    def dump_comment_line(self, obj: yaslha.line.CommentLine)->str:
        return obj.line

    def dump_block_line(self, obj: yaslha.line.BlockLine)->str:
        q_str = '' if obj.q is None else 'Q={}'.format(self._e_float(obj.q))
        body = '{} {} {}'.format(self.block_str, obj.name.upper(), q_str)
        return '{:23}   # {}'.format(body, obj.comment.lstrip()).rstrip()

    def dump_info_line(self, obj: yaslha.line.InfoLine, block_name: str)->str:
        lines = list()
        for i, v in enumerate(obj.value):
            c = obj.comment[i] if len(obj.comment) > i else ''
            lines.append(' {:>5}   {:16}   # {}'.format(obj.key, v, c).rstrip())
        return '\n'.join(lines)

    def dump_value_line(self, obj: yaslha.line.ValueLine, block_name: str)->str:
        if block_name == 'MASS' and isinstance(obj.key, int):
            return ' {:>9}   {}   # {}'.format(obj.key, self._e_float(obj.value), obj.comment.lstrip()).rstrip()

        if isinstance(obj.key, tuple):
            key_str = ' '.join(['{:>2}'.format(i) for i in obj.key])
        else:
            key_str = '{:>5}'.format('' if obj.key is None else obj.key)

        if isinstance(obj.value, int):
            value_str = '{:>10}      '.format(obj.value)
        elif isinstance(obj.value, float):
            value_str = self._e_float(obj.value)
        else:
            value_str = '{:<16}'.format(obj.value)
        return ' {}   {}   # {}'.format(key_str, value_str, obj.comment.lstrip()).rstrip()

    def dump_decay(self, decay: 'yaslha.Decay', document_block: bool = False):
        head = [decay.head_line()]  # type: List[yaslha.line.AbsLine]
        body, key_order = self._decay_lines_with_key_order(decay)
        tail = []                   # type: List[yaslha.line.AbsLine]
        if self.comments_preserve.keep_line():
            pre_comment = cast(List[yaslha.line.AbsLine], decay.line_comment(CommentPosition.Prefix))
            head_comment = cast(List[yaslha.line.AbsLine], decay.line_comment(CommentPosition.Heading))
            head = pre_comment + head + head_comment
            tail = cast(List[yaslha.line.AbsLine], decay.line_comment(CommentPosition.Suffix))

        lines = _clean([self.dump_line(obj) for obj in head + body + tail])
        if document_block:
            lines = [self.comment_out(line) for line in lines]
        return '\n'.join(lines) + '\n'

    def dump_decayblock_line(self, obj: yaslha.line.DecayBlockLine)->str:
        return '{} {:>9}   {}   # {}'.format(
            self.decay_str, obj.pid, self._e_float(obj.width), obj.comment.lstrip()).rstrip()

    def dump_decay_line(self, obj: yaslha.line.DecayLine)->str:
        ids_str = ''.join(['{:>9} '.format(i) for i in obj.key])
        return '   {}   {:>2}   {}  # {}'.format(
            self._e_float(obj.value), len(obj.key), ids_str, obj.comment.lstrip()).rstrip()


class AbsMarshalDumper(AbsDumper):
    SCHEME_VERSION = 1

    def __init__(self, **kwargs)->None:
        super().__init__(**kwargs)

    def marshal(self, slha: 'yaslha.SLHA')->Mapping:
        return _clean(OrderedDict([
            ('FORMAT', OrderedDict([
                ('TYPE', 'SLHA'),
                ('FORMATTER', '{} {}'.format(yaslha.__pkgname__, yaslha.__version__)),
                ('SCHEME', self.SCHEME_VERSION),
            ])),
            ('BLOCK', OrderedDict([(b.name, self.marshal_block(b)) for b in self._blocks_sorted(slha)])),
            ('DECAY', OrderedDict([(d.pid, self.marshal_decay(d)) for d in self._decays_sorted(slha)])),
            ('tail_comment', [v.line for v in slha.tail_comment] if self.comments_preserve.keep_line() else []),
        ]))

    def marshal_block(self, block: 'yaslha.Block')->Mapping[Any, Any]:
        data = OrderedDict([('info', None),
                            ('values', None),
                            ('comments', OrderedDict())])  # type: MutableMapping[str, Any]
        values, key_order = self._block_lines_with_key_order(block)
        values_without_comment_lines = _flatten([v for v in values if not isinstance(v, yaslha.line.CommentLine)])
        if block.q:
            data['info'] = ['Q=', block.q]
        if self.comments_preserve.keep_line():
            for c_pos in CommentPosition:
                if block.line_comment(c_pos):
                    data['comments'][c_pos.name] = [v.line for v in block.line_comment(c_pos)]
        if self.comments_preserve.keep_tail():
            present_keys = block.line_comment_keys()
            for c_key in key_order:
                if c_key in present_keys:
                    data['comments'][c_key] = [v.line for v in block.line_comment(c_key)]

        data['values'] = list([self.marshal_line(line) for line in values_without_comment_lines])
        return _clean(data)

    def marshal_decay(self, decay: 'yaslha.Decay')->Mapping[Any, Any]:
        data = OrderedDict([('info', [decay.width]),
                            ('values', None),
                            ('comments', OrderedDict())])  # type: MutableMapping[str, Any]
        values, key_order = self._decay_lines_with_key_order(decay)
        values_without_comment_lines = _flatten([v for v in values if not isinstance(v, yaslha.line.CommentLine)])

        if self.comments_preserve.keep_line():
            for c_pos in yaslha.line.CommentPosition:
                if decay.line_comment(c_pos):
                    data['comments'][c_pos.name] = [v.line for v in decay.line_comment(c_pos)]
        if self.comments_preserve.keep_tail():
            present_keys = decay.line_comment_keys()
            for c_key in key_order:
                if c_key in present_keys:
                    data['comments'][str(c_key)] = [v.line for v in decay.line_comment(c_key)]

        data['values'] = list([self.marshal_line(line) for line in values_without_comment_lines])
        return _clean(data)

    def marshal_line(self, line: yaslha.line.AbsLine) -> Any:
        if isinstance(line, yaslha.line.DecayLine):
            return _flatten([line.value, len(line.key), line.key])
        elif isinstance(line, yaslha.line.CommentLine):
            pass
        elif line.key is None:
            return [line.value]
        else:
            return _flatten([line.key, line.value])


class YAMLDumper(AbsMarshalDumper):
    def __init__(self, **kwargs)->None:
        super().__init__(**kwargs)
        self.yaml = ruamel.yaml.YAML()
        self.yaml.default_flow_style = None

        # we need not it is marked as omap (OrderedDict); it could be just a dict as an output.
        # (but we may change the mind....)
        self.yaml.representer.yaml_representers[OrderedDict] = self.yaml.representer.yaml_representers[dict]
        # # another idea...
        # def represent_list(self, data):
        #     flow_style = all(isinstance(i, str) or not hasattr(i, '__iter__') for i in data)
        #     return self.represent_sequence(u'tag:yaml.org,2002:seq', data, flow_style=flow_style)
        # self.yaml.representer.yaml_representers[list] = represent_list

    def dump(self, data: 'yaslha.SLHA')->str:
        stream = ruamel.yaml.compat.StringIO()
        self.yaml.dump(self.marshal(data), stream)
        return stream.getvalue()


class JSONDumper(AbsMarshalDumper):
    def __init__(self, **kwargs)->None:
        super().__init__(**kwargs)
        self.indent = 2

    def dump(self, slha: 'yaslha.SLHA')->str:
        return json.dumps(self.marshal(slha), indent=self.indent)
