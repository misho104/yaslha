"""Package to handle SLHA-format files and data."""

import pathlib
from typing import Any, Optional, Union

import yaslha.block
import yaslha.comment
import yaslha.config
import yaslha.dumper
import yaslha.line
import yaslha.parser
import yaslha.slha

__pkgname__ = "yaslha"
__version__ = "0.2.0"
__author__ = "Sho Iwamoto / Misho"
__license__ = "MIT"

SLHA = yaslha.slha.SLHA
Block = yaslha.block.Block
InfoBlock = yaslha.block.InfoBlock
Decay = yaslha.block.Decay

cfg = yaslha.config.Config()


def parse(text, input_type="AUTO", parser=None, **kwargs):
    # type: (str, str, Any, Any)->SLHA
    """Parse a text to return an SLHA object."""
    if parser is None:
        if input_type.upper() == "AUTO":
            # TODO: implement auto-parser
            parser = yaslha.parser.SLHAParser(**kwargs)
        elif input_type.upper() == "JSON":
            raise NotImplementedError
        elif input_type.upper() == "YAML":
            raise NotImplementedError
        else:
            parser = yaslha.parser.SLHAParser(**kwargs)
    return parser.parse(text)


def dump(slha, output_type="SLHA", dumper=None, **kwargs):
    # type: (SLHA, str, Optional[yaslha.dumper.AbsDumper], Any)->str
    """Output a dumped string of an SLHA object."""
    if dumper is None:
        if output_type.upper() == "JSON":
            dumper = yaslha.dumper.JSONDumper(**kwargs)
        elif output_type.upper() == "YAML":
            dumper = yaslha.dumper.YAMLDumper(**kwargs)
        else:
            dumper = yaslha.dumper.SLHADumper(**kwargs)
    return dumper.dump(slha)


def parse_file(path, **kwargs):
    # type: (Union[str, pathlib.Path], Any)->SLHA
    """Parse a file to return an SLHA object."""
    if isinstance(path, str):
        path = pathlib.Path(path)
    return parse(path.read_text(), **kwargs)


def dump_file(data, path, **kwargs):
    # type: (SLHA, Union[str, pathlib.Path], Any)->None
    """Write into a file a dumped string of an SLHA object."""
    with open(str(path), "w") as f:
        f.write(dump(data, **kwargs))
