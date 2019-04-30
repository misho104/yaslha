import collections
from abc import ABCMeta, abstractmethod
from typing import Any, Optional, TypeVar, Union, overload

K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T", None, Any)

class _OrderedNormalizedDict(collections.OrderedDict[K, V], metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def _n(self, key: K) -> K: ...
    def __init__(self, *args: Any, **kwds: Any) -> None: ...
    def __setitem__(self, key: K, value: V) -> None: ...
    def __getitem__(self, key: K) -> V: ...
    def __delitem__(self, key: K) -> None: ...
    def __contains__(self, key: Any) -> bool: ...
    @overload
    def get(self, key: K) -> Optional[V]: ...
    @overload
    def get(self, key: Any, default: Union[V, T]) -> Union[V, T]: ...
    @overload
    def pop(self, key: K) -> V: ...
    @overload
    def pop(self, key: K, default: Union[V, T] = ...) -> Union[V, T]: ...
    def move_to_end(self, key: K, last: bool = True) -> None: ...

class OrderedCaseInsensitiveDict(_OrderedNormalizedDict[K, V]):
    @classmethod
    def _n(self, key: K) -> K: ...

class OrderedTupleOrderInsensitiveDict(_OrderedNormalizedDict[K, V]):
    @classmethod
    def _n(self, key: K) -> K: ...