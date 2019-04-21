"""Definitions of customized collection classes."""

from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from typing import Any, Generic, TypeVar, Union, cast

K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T", None, Any)

_not_specified = object()


class _OrderedNormalizedDict(OrderedDict, Generic[K, V], metaclass=ABCMeta):
    """Abstract class for normalized OrderedDict.

    Normalization is given by the class method `_n`.
    """

    @classmethod
    @abstractmethod
    def _n(self, key: K) -> K:
        pass

    def __init__(self, *args: Any, **kwds: Any) -> None:
        """Initialize an ordered dictionary."""
        # first construct a temporal dict
        tmp = OrderedDict(*args, **kwds)
        for k, v in tmp.items():
            self.__setitem__(k, v)

    def __setitem__(self, key: K, value: V) -> None:
        super().__setitem__(self._n(key), value)

    def __getitem__(self, key: K) -> V:
        return cast(V, super().__getitem__(self._n(key)))

    def __delitem__(self, key: K) -> None:
        super().__delitem__(self._n(key))

    def __contains__(self, key: Any) -> bool:
        return super().__contains__(self._n(key))

    # def get(self, k: _KT, default: Union[_VT_co, _T]) -> Union[_VT_co, _T]: ...

    def get(self, key: Any, default: Union[V, T] = None) -> Union[V, T]:
        return self[key] if key in self else default

    def pop(self, key: K, default: Union[V, T, object] = _not_specified) -> Union[V, T]:
        if default == _not_specified:
            return cast("V", super().pop(self._n(key)))
        else:
            return super().pop(self._n(key), default=default)

    def move_to_end(self, key: K, last: bool = True) -> None:
        return super().move_to_end(self._n(key), last)


class OrderedCaseInsensitiveDict(_OrderedNormalizedDict[K, V]):
    """OrderedDict with case-insensitive keys.

    Keys are identified as case-insensitive. For a tuple as a key, the elements
    of the tuples are not normalized and remain case-sensitive.
    """

    @classmethod
    def _n(self, key: K) -> K:
        return key.upper() if hasattr(key, "upper") else key  # type: ignore


class OrderedTupleOrderInsensitiveDict(_OrderedNormalizedDict[K, V]):
    """OrderedDict with neglecting order of tuple elements.

    The identification is applied only if ```isinstance(key, tuple)``` is True,
    and only to the top-level elements.
    """

    @classmethod
    def _n(self, key: K) -> K:
        return tuple(sorted(key)) if isinstance(key, tuple) else key  # type: ignore
