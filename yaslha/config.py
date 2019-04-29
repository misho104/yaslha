"""Configuration handlers."""

import collections.abc
import configparser
import enum
import os
import pathlib
from typing import Any, List, MutableMapping, Type, TypeVar

CONFIG_FILES = [
    str(pathlib.Path(__file__).with_name("yaslha.cfg.default")),
    os.path.expanduser("~/.yaslha.cfg"),
    "yaslha.cfg",
]  # latter overrides former

EnumType = TypeVar("EnumType", bound=enum.Enum)


class SectionWrapper:
    """A wrapper class of `configparser.SectionProxy`."""

    def __init__(self, data: configparser.SectionProxy) -> None:
        self._data = data  # type: configparser.SectionProxy
        self.override = {}  # type: MutableMapping[str, Any]

    def __getattr__(self, name: str) -> Any:
        return self._data.__getattribute__(name)

    def __getitem__(self, key: str) -> Any:
        if key in self.override:
            return self.override[key]
        if key in self._data:
            return self._data[key]
        raise KeyError(key)

    def get_enum(self, key: str, enum_class: Type[EnumType]) -> EnumType:
        """Get an item as an Enum-class object."""
        if key in self.override:
            return self.override[key]  # type: ignore
        if key in self._data:
            value = self._data[key].lower()
            for i in enum_class:
                if i.name.lower() == value:
                    return i
        raise KeyError(key)

    def get_list(self, key: str) -> List[str]:
        """Get a List[str] object."""
        key_for_a_list = "{}@list".format(key)
        if key in self.override:
            value = self.override[key]
        elif key_for_a_list in self._data:
            value = self._data[key_for_a_list]
        else:
            raise KeyError(key)
        if isinstance(value, str):
            return [v for v in value.split(" ") if v]
        elif isinstance(value, collections.abc.Sequence):
            return [str(v) for v in value]
        else:
            raise TypeError(value)


class Config(configparser.ConfigParser):
    """Dictionary to store the configurations."""

    def __init__(self) -> None:
        super().__init__(inline_comment_prefixes="#")
        super().read(CONFIG_FILES)

    def __getitem__(self, key: Any) -> Any:
        return SectionWrapper(super().__getitem__(key))
