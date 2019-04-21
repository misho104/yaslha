"""Module of a class to handle comment interface."""

from typing import Any, Generic, List, Optional, TypeVar, Union, overload

from typing_extensions import Literal

from yaslha._line import DecayKeyType, InfoKeyType, KeyType
from yaslha.block import GenericBlock

KTG = TypeVar("KTG", KeyType, InfoKeyType, DecayKeyType)
CT = TypeVar("CT", str, List[str])
HEAD = Literal["head"]

class CommentInterface(Generic[KTG, CT]):
    _block: "GenericBlock[KTG, CT]"
    _pre: "PreCommentInterface[KTG, CT]"
    def __init__(self, block: "GenericBlock[KTG, CT]") -> None: ...
    @property
    def pre(self) -> "PreCommentInterface[KTG, CT]": ...
    @overload
    def __getitem__(self, key: HEAD) -> str: ...
    @overload
    def __getitem__(self, key: KTG) -> CT: ...
    # def __getitem__(self, key: Union[KTG, HEAD]) -> Union[CT, str]: ...
    @overload
    def __setitem__(self, key: HEAD, value: Optional[str]) -> None: ...
    @overload
    def __setitem__(self, key: KTG, value: Optional[CT]) -> None: ...
    # def __setitem__(self, key: Union[KTG, HEAD], value: Union[CT, str]) -> None: ...
    @overload
    def __call__(self, key: HEAD, **kw: Any) -> str: ...
    @overload
    def __call__(self, key: KTG, **kw: Any) -> CT: ...
    # def __call__(self, key: Union[KTG, HEAD], **kw: Any) -> Union[CT, str]: ...

class PreCommentInterface(Generic[KTG, CT]):
    _block: "GenericBlock[KTG, CT]"
    def __init__(self, block: "GenericBlock[KTG, CT]"): ...
    def __getitem__(self, key: Union[KTG, HEAD]) -> List[str]: ...
    def __setitem__(
        self, key: Union[KTG, HEAD], value: Optional[List[str]]
    ) -> None: ...
    def __call__(self, key: Union[KTG, HEAD], **kw: Any) -> List[str]: ...
