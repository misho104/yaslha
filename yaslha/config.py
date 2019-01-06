import enum
import os
import pathlib
import configparser
from typing import Mapping, Union, Dict, Any, TypeVar, Tuple, Optional  # noqa: F401


CONFIG_FILES = [
    str(pathlib.Path(__file__).with_name('yaslha.cfg.default')),
    os.path.expanduser('~/.yaslha.cfg'),
    'yaslha.cfg']  # latter overrides former


class ConfigDict(Dict[str, Any]):
    def value(self, key, override=None, typ=None):
        # type: (str, Any, Any)->Any
        configuration = self[key]

        if typ and issubclass(typ, enum.Enum):
            c = None
            for i in typ:
                if configuration.lower() == i.name.lower():
                    c = i
            configuration = c or list(typ)[0]
        elif typ == bool:
            configuration = False if configuration.lower() in ['false', 'None', '0'] else bool(configuration)

        return configuration if override is None else override


def read_config():
    # type: ()->ConfigDict
    config = configparser.ConfigParser(inline_comment_prefixes='#')
    config.read(CONFIG_FILES)
    return compose_dict(config)


def compose_dict(config):
    # type: (Union[Mapping[str, Any], configparser.ConfigParser])->ConfigDict
    return ConfigDict(compose_dict_sub(k, v) for k, v in config.items())


def compose_dict_sub(key, value):
    # type: (str, Any)->Tuple[str, Any]
    if hasattr(value, 'items'):
        return (key, compose_dict(value))
    elif key.endswith('@list'):
        return key[:-5], [v for v in value.split(' ') if v] if value else []
    else:
        return key, value
