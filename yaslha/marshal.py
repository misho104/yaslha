import yaslha


def _clean(obj: dict)->dict:
    return {k: v for k, v in obj.items() if v}


def _flatten(obj: list) -> list:
    return [element
            for item in obj
            for element in (_flatten(item) if hasattr(item, '__iter__') and not isinstance(item, str) else [item])]


class Marshal:
    SCHEME_VERSION = 1

    def dump(self, slha: 'yaslha.SLHA')->dict:
        return _clean({
            'FORMAT': {
                'TYPE': 'SLHA',
                'FORMATTER': f'{yaslha.__pkgname__} {yaslha.__version__}',
                'SCHEME': self.SCHEME_VERSION
            },
            'BLOCK': dict([(b.name, self.dump_block(b)) for b in slha.blocks.values()]),
            'DECAY': dict([(d.pid, self.dump_decay(d)) for d in slha.decays.values()])
        })

    def dump_block(self, block: 'yaslha.Block')->dict:
        data = {'info': ['Q=', block.q]} if block.q is not None else {}
        data['values'] = list([self.dump_line(line) for line in block.value_lines()])
        return _clean(data)

    def dump_decay(self, decay: 'yaslha.Decay')->dict:
        data = {'info': [decay.width]}
        data['values'] = list([self.dump_line(line) for line in decay.value_lines()])
        return _clean(data)

    def dump_line(self, line: yaslha.line.AbsLine) -> list:
        if isinstance(line, yaslha.line.DecayLine):
            return _flatten([line.value, len(line.key), line.key])
        elif line.key is None:
            return [line.value]
        else:
            return _flatten([line.key, line.value])
