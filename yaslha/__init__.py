import pathlib
from typing import Union, Mapping  # noqa: F401

import yaslha.config
import yaslha.parser
import yaslha.dumper
from yaslha.core import SLHA, Block, Decay  # noqa: F401


__pkgname__ = 'yaslha'
__version__ = '0.0.6'
__author__ = 'Sho Iwamoto / Misho'
__license__ = 'MIT'

cfg = yaslha.config.read_config()  # type: Mapping


def parse(text: Union[str, pathlib.Path], **kwargs)->SLHA:
    if isinstance(text, pathlib.Path):
        with open(str(text)) as f:
            text = f.read()
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


def parse_file(path: Union[str, pathlib.Path], **kwargs)->SLHA:
    if isinstance(path, str):
        path = pathlib.Path(path)
    return parse(path, **kwargs)


def dump_file(data: SLHA, path: Union[str, pathlib.Path], **kwargs)->None:
    with open(str(path), 'w') as f:
        f.write(dump(data, **kwargs))
