"""Module of a class to handle comment interface."""

import logging
from typing import TYPE_CHECKING, Generic, List, TypeVar, Union

from typing_extensions import Literal

from yaslha._line import format_comment

if TYPE_CHECKING:
    from yaslha.block import GenericBlock
    from yaslha._line import DecayKeyType, KeyType, InfoKeyType  # noqa: F401

KTG = TypeVar("KTG", "KeyType", "InfoKeyType", "DecayKeyType")
CT = TypeVar("CT", str, List[str])
HEAD = Literal["head"]

logger = logging.getLogger(__name__)


class CommentInterface(Generic[KTG, CT]):
    """Accessor object to the comments in blocks."""

    def __init__(self, block: "GenericBlock[KTG, CT]") -> None:
        self._block = block  # type: GenericBlock[KTG, CT]
        self._pre = PreCommentInterface(block)  # type: PreCommentInterface[KTG, CT]

    @property
    def pre(self) -> "PreCommentInterface[KTG, CT]":
        """Return pre-comment interface."""
        return self._pre

    def __getitem__(self, key: Union[KTG, HEAD]) -> Union[CT, str]:  # noqa: F811
        """Return comment."""
        if key == "head":
            return self._block.head.comment
        else:
            return self._block._get_comment(key)

    def __setitem__(self, key: Union[KTG, HEAD], value: Union[CT, str, None]) -> None:
        """Set comment."""
        if key == "head":
            self._block.head.comment = value or ""
        else:
            self._block._set_comment(key, value)

    def __call__(self, key: Union[KTG, HEAD], **kw: bool) -> Union[CT, str]:
        """Return comment in specified format."""
        return format_comment(self.__getitem__(key), **kw)


class PreCommentInterface(Generic[KTG, CT]):
    """Accessor object to the pre-line comments in blocks."""

    def __init__(self, block: "GenericBlock[KTG, CT]"):
        self._block = block  # type: GenericBlock[KTG, CT]

    def __getitem__(self, key: Union[KTG, HEAD]) -> List[str]:
        """Return pre-line comment."""
        if key == "head":
            return self._block.head.pre_comment
        else:
            return self._block._get_pre_comment(key)

    def __setitem__(self, key: Union[KTG, HEAD], value: Union[List[str], None]) -> None:
        """Set pre-line comment."""
        if key == "head":
            self._block.head.pre_comment = value or []
        else:
            self._block._set_pre_comment(key, value)

    def __call__(self, key: Union[KTG, HEAD], **kw: bool) -> List[str]:
        """Return pre-line comment in specified format."""
        return format_comment(self.__getitem__(key), **kw)
