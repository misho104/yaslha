import pathlib
from typing import Union, Mapping, Any, Optional  # noqa: F401

import yaslha.config
import yaslha.parser
import yaslha.dumper
from yaslha.core import SLHA, Block, Decay  # noqa: F401


__pkgname__ = 'yaslha'
__version__ = '0.1.0'
__author__ = 'Sho Iwamoto / Misho'
__license__ = 'MIT'

cfg = yaslha.config.read_config()  # type: Mapping[str, Any]


def parse(text, **kwargs):
    # type: (Union[str, pathlib.Path], Any)->SLHA
    if isinstance(text, pathlib.Path):
        with open(str(text)) as f:
            text = f.read()
    parser = yaslha.parser.SLHAParser(**kwargs)
    return parser.parse(text)


def dump(data, output_type='', dumper=None, **kwargs):
    # type: (SLHA, str, Optional[yaslha.dumper.AbsDumper], Any)->str
    if dumper is None:
        if output_type.upper() == 'JSON':
            dumper = yaslha.dumper.JSONDumper(**kwargs)
        elif output_type.upper() == 'YAML':
            dumper = yaslha.dumper.YAMLDumper(**kwargs)
        else:
            dumper = yaslha.dumper.SLHADumper(**kwargs)
    return data.dump(dumper=dumper)


def parse_file(path, **kwargs):
    # type: (Union[str, pathlib.Path], Any)->SLHA
    if isinstance(path, str):
        path = pathlib.Path(path)
    return parse(path, **kwargs)


def dump_file(data, path, **kwargs):
    # type: (SLHA, Union[str, pathlib.Path], Any)->None
    with open(str(path), 'w') as f:
        f.write(dump(data, **kwargs))
