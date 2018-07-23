import json
from typing import Type, Optional, MutableMapping, Any, Mapping, List  # noqa: F401
import ruamel.yaml
import yaslha
import yaslha.line


def _clean(obj: Any)->Any:
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items() if not (v is None or (hasattr(v, '__len__') and len(v) == 0))}
    else:
        return obj


def _flatten(obj: List)->List:
    return [element
            for item in obj
            for element in (_flatten(item) if hasattr(item, '__iter__') and not isinstance(item, str) else [item])]


class AbsDumper:
    def __init__(self)->None:
        pass

    def dump(self, block: 'yaslha.SLHA')->str:
        return NotImplemented


class SLHADumper(AbsDumper):
    def dump(self, slha: 'yaslha.SLHA')->str:
        blocks = [self.dump_block(block) for block in slha.blocks.values()]
        decays = [self.dump_decay(decay) for decay in slha.decays.values()]
        return ''.join(blocks) + ''.join(decays)

    def dump_block(self, block: 'yaslha.Block')->str:
        return '\n'.join([self.dump_line(line, block.name) for line in block.lines()]) + '\n'

    def dump_line(self, obj: yaslha.line.AbsLine, block_name: Optional[str]=None):
        # TODO: rewrite using singledispatcher
        if isinstance(obj, yaslha.line.CommentLine):
            return self.dump_comment_line(obj)
        elif isinstance(obj, yaslha.line.BlockLine):
            return self.dump_block_line(obj)
        elif isinstance(obj, yaslha.line.DecayBlockLine):
            return self.dump_decayblock_line(obj)
        elif isinstance(obj, yaslha.line.DecayLine):
            return self.dump_decay_line(obj)
        elif isinstance(obj, yaslha.line.InfoLine):
            return self.dump_info_line(obj, block_name)
        elif isinstance(obj, yaslha.line.ValueLine):
            return self.dump_value_line(obj, block_name)

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
        return '\n'.join([self.dump_line(line) for line in decay.lines()]) + '\n'

    def dump_decayblock_line(self, obj: yaslha.line.DecayBlockLine)->str:
        return f'Decay {obj.pid:>9}   {obj.width:16.8E}   # {obj.comment.strip()}'.rstrip()

    def dump_decay_line(self, obj: yaslha.line.DecayLine)->str:
        ids_str = ''.join([f'{i:>9} ' for i in obj.key])
        return f'   {obj.value:16.8E}   {len(obj.key):>2}   {ids_str}  # {obj.comment.strip()}'.rstrip()


class AbsMarshalDumper(AbsDumper):
    SCHEME_VERSION = 1

    def __init__(self, **kwargs)->None:
        super().__init__()

    def marshal(self, slha: 'yaslha.SLHA')->Mapping:
        return _clean({
            'FORMAT': {
                'TYPE': 'SLHA',
                'FORMATTER': f'{yaslha.__pkgname__} {yaslha.__version__}',
                'SCHEME': self.SCHEME_VERSION
            },
            'BLOCK': dict([(b.name, self.marshal_block(b)) for b in slha.blocks.values()]),
            'DECAY': dict([(d.pid, self.marshal_decay(d)) for d in slha.decays.values()])
        })

    def marshal_block(self, block: 'yaslha.Block')->Mapping[Any, Any]:
        data = {'info': ['Q=', block.q]} if block.q is not None else {}   # type: MutableMapping[Any, Any]
        data['values'] = list([self.marshal_line(line) for line in block.value_lines()])
        return _clean(data)

    def marshal_decay(self, decay: 'yaslha.Decay')->Mapping[Any, Any]:
        data = {'info': [decay.width]}  # type: MutableMapping[Any, Any]
        data['values'] = list([self.marshal_line(line) for line in decay.value_lines()])
        return _clean(data)

    def marshal_line(self, line: yaslha.line.AbsLine) -> Any:
        if isinstance(line, yaslha.line.DecayLine):
            return _flatten([line.value, len(line.key), line.key])
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
