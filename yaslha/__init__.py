from yaslha.core import SLHA, Block, Decay  # noqa: F401
import yaslha.parser
import yaslha.dumper

__pkgname__ = 'yaslha'
__version__ = '0.0.3'
__author__ = 'Sho Iwamoto / Misho'
__license__ = 'MIT'


def parse(text: str, **kwargs)->SLHA:
    parser = yaslha.parser.SLHAParser(**kwargs)
    return parser.parse(text)


def dump(data: SLHA, output_type=None, dumper=None, **kwargs)->str:
    if dumper is None:
        if output_type.upper() == 'JSON':
            dumper = yaslha.dumper.JSONDumper(**kwargs)
        elif output_type.upper() == 'YAML':
            dumper = yaslha.dumper.YAMLDumper(**kwargs)
        else:
            dumper = yaslha.dumper.SLHADumper(**kwargs)
    return data.dump(dumper=dumper)
