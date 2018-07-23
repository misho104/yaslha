import enum
import json
import re
from typing import cast, Type, Optional, MutableMapping, Any, Tuple, Mapping, List  # noqa: F401

import ruamel.yaml

import yaslha
import yaslha.line
from yaslha.line import CommentPosition
import yaslha.exceptions as exceptions
import yaslha.utility
from yaslha.utility import _clean, _flatten


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
                 blocks_order: BlocksOrder = BlocksOrder.DEFAULT,
                 values_order: ValuesOrder = ValuesOrder.DEFAULT,
                 comments_preserve: CommentsPreserve = CommentsPreserve.ALL,
                 )->None:
        self.blocks_order = blocks_order
        self.values_order = values_order
        self.comments_preserve = comments_preserve

    def dump(self, block: 'yaslha.SLHA')->str:
        return NotImplemented

    def _blocks_sorted(self, slha: 'yaslha.SLHA')->List['yaslha.Block']:
        if self.blocks_order == BlocksOrder.KEEP:
            return slha.blocks.values()
        block_names = slha.blocks.keys()
        if self.blocks_order == BlocksOrder.ABC:
            block_names.sort()
        else:
            block_names = yaslha.utility.sort_blocks_default(block_names)
        return [slha.blocks[name] for name in block_names]

    def _decays_sorted(self, slha: 'yaslha.SLHA')->List['yaslha.Decay']:
        if self.values_order == ValuesOrder.KEEP:
            return slha.decays.values()
        pids = slha.decays.keys()
        if self.values_order == ValuesOrder.SORTED:
            pids.sort()
        else:
            pids = yaslha.utility.sort_pids_default(pids)
        return [slha.decays[pid] for pid in pids]

    def _block_lines_with_key_order(self, block: 'yaslha.Block')->Tuple[List[yaslha.line.AbsLine], List[yaslha.line.KeyType]]:
        value_lines = block.value_lines(with_comment_lines=self.comments_preserve.keep_line())

        keys = list(value_lines.keys())
        if self.values_order == ValuesOrder.DEFAULT and block.name == 'MASS':
            keys = yaslha.utility.sort_pids_default(keys)
        elif self.values_order != ValuesOrder.KEEP:
            keys.sort()
        lines = _flatten([cast(yaslha.line.AbsLine, value_lines[key]) for key in keys])
        return lines, keys

    def _decay_lines_with_key_order(self, decay: 'yaslha.Decay')->Tuple[List[yaslha.line.AbsLine], List[yaslha.line.KeyType]]:
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

    def dump(self, slha: 'yaslha.SLHA')->str:
        blocks = [self.dump_block(block) for block in self._blocks_sorted(slha)]
        decays = [self.dump_decay(decay) for decay in self._decays_sorted(slha)]
        if self.comments_preserve.keep_line():
            tail_comment = [v.line for v in slha.tail_comment]
        else:
            tail_comment = []
        return ''.join(blocks) + ''.join(decays) + '\n'.join(tail_comment)

    def dump_block(self, block: 'yaslha.Block')->str:
        head = [block.head_line()]  # type: List[yaslha.line.AbsLine]
        body, key_order = self._block_lines_with_key_order(block)
        tail = []                   # type: List[yaslha.line.AbsLine]
        if self.comments_preserve.keep_line():
            pre_comment = cast(List[yaslha.line.AbsLine], block.line_comment(CommentPosition.Prefix))
            head_comment = cast(List[yaslha.line.AbsLine], block.line_comment(CommentPosition.Heading))
            head = pre_comment + head + head_comment
            tail = cast(List[yaslha.line.AbsLine], block.line_comment(CommentPosition.Suffix))

        return '\n'.join([self.dump_line(obj, block_name=block.name) for obj in head + body + tail]) + '\n'

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
        q_str = '' if obj.q is None else f'Q={float(obj.q):15.8E}'
        body = f'Block {obj.name.upper()} {q_str}'
        return f'{body:23}   # {obj.comment.strip()}'.rstrip()

    def dump_info_line(self, obj: yaslha.line.InfoLine, block_name: str)->str:
        lines = list()
        for i, v in enumerate(obj.value):
            c = obj.comment[i] if len(obj.comment) > i else ''
            lines.append(f' {obj.key:>5}   {v:16}   # {c}'.rstrip())
        return '\n'.join(lines)

    def dump_value_line(self, obj: yaslha.line.ValueLine, block_name: str)->str:
        if block_name == 'MASS' and isinstance(obj.key, int):
            return f' {obj.key:>9}   {obj.value:16.8E}   # {obj.comment.strip()}'.rstrip()

        if isinstance(obj.key, tuple):
            key_str = ' '.join([f'{i:>2}' for i in obj.key])
        else:
            key_str = f'{"" if obj.key is None else obj.key:>5}'

        if isinstance(obj.value, int):
            value_str = f'{obj.value:>10}      '
        elif isinstance(obj.value, float):
            value_str = f'{obj.value:16.8E}'
        else:
            value_str = f'{obj.value:<16}'
        return f' {key_str}   {value_str}   # {obj.comment.strip()}'.rstrip()

    def dump_decay(self, decay: 'yaslha.Decay'):
        head = [decay.head_line()]  # type: List[yaslha.line.AbsLine]
        body, key_order = self._decay_lines_with_key_order(decay)
        tail = []                   # type: List[yaslha.line.AbsLine]
        if self.comments_preserve.keep_line():
            pre_comment = cast(List[yaslha.line.AbsLine], decay.line_comment(CommentPosition.Prefix))
            head_comment = cast(List[yaslha.line.AbsLine], decay.line_comment(CommentPosition.Heading))
            head = pre_comment + head + head_comment
            tail = cast(List[yaslha.line.AbsLine], decay.line_comment(CommentPosition.Suffix))

        return '\n'.join([self.dump_line(obj) for obj in head + body + tail]) + '\n'

    def dump_decayblock_line(self, obj: yaslha.line.DecayBlockLine)->str:
        return f'Decay {obj.pid:>9}   {obj.width:16.8E}   # {obj.comment.strip()}'.rstrip()

    def dump_decay_line(self, obj: yaslha.line.DecayLine)->str:
        ids_str = ''.join([f'{i:>9} ' for i in obj.key])
        return f'   {obj.value:16.8E}   {len(obj.key):>2}   {ids_str}  # {obj.comment.strip()}'.rstrip()


class AbsMarshalDumper(AbsDumper):
    SCHEME_VERSION = 1

    def __init__(self, **kwargs)->None:
        super().__init__(**kwargs)

    def marshal(self, slha: 'yaslha.SLHA')->Mapping:
        return _clean({
            'FORMAT': {
                'TYPE': 'SLHA',
                'FORMATTER': f'{yaslha.__pkgname__} {yaslha.__version__}',
                'SCHEME': self.SCHEME_VERSION
            },
            'BLOCK': dict([(b.name, self.marshal_block(b)) for b in self._blocks_sorted(slha)]),
            'DECAY': dict([(d.pid, self.marshal_decay(d)) for d in self._decays_sorted(slha)]),
            'tail_comment': [v.line for v in slha.tail_comment] if self.comments_preserve.keep_line() else [],
        })

    def marshal_block(self, block: 'yaslha.Block')->Mapping[Any, Any]:
        data = {'info': None, 'values': None, 'comments': dict()}  # type: MutableMapping[str, Any]
        values, key_order = self._block_lines_with_key_order(block)
        values_without_comment_lines = _flatten([v for v in values if not isinstance(v, yaslha.line.CommentLine)])
        if block.q:
            data['info'] = ['Q=', block.q]
        if self.comments_preserve.keep_line():
            for c_pos in yaslha.line.CommentPosition:
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
        data = {'info': [decay.width], 'values': None, 'comments': dict()}  # type: MutableMapping[str, Any]
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
