"""Unit test of `_collections` module."""

import collections
import logging
import unittest
from typing import Any, MutableMapping

import pytest

from yaslha._collections import OrderedCaseInsensitiveDict as oci_dict
from yaslha._collections import OrderedTupleOrderInsensitiveDict as toi_dict

logger = logging.getLogger("test_info")


class TestOrderedCaseInsensitiveDict(unittest.TestCase):
    """Unit test of `OrderedCaseInsensitiveDict`."""

    def setUp(self):
        self.d = oci_dict()  # type: oci_dict[Any, Any]
        self.d["FIRST"] = 100
        self.d[2] = None
        self.d[("Third", 0)] = (1, 2, 3)  # inner elements are not normalized
        self.d[1] = "AnB"

    def test_init_by_list(self):
        d = oci_dict(
            [("a", 10), ("B", 30), (None, "AnB"), (1, "300aBC")]
        )  # type: oci_dict[Any, Any]
        assert d["A"] == 10
        assert d["b"] == 30
        assert d["B"] == 30
        assert d[None] == "AnB"
        assert d[1] == "300aBC"
        assert list(d.keys()) == ["A", "B", None, 1]

    def test_init_by_keywords(self):
        d = oci_dict(
            FiRST=3, SeCoND=None, third=(1, 2, 3), lAST="AnB"
        )  # type: oci_dict[Any, Any]
        assert d["FIRST"] == 3
        assert d["second"] is None
        assert d["third"] == (1, 2, 3)
        assert d["last"] == "AnB"

    def test_contains(self):
        assert "first" in self.d
        assert "FIRst" in self.d
        assert "_first" not in self.d

        assert None not in self.d
        assert 2 in self.d
        assert 3 not in self.d

        assert ("Third", 0) in self.d
        assert ("third", 0) not in self.d

    def test_delitem(self):
        del self.d["FIrST"]
        del self.d[1]
        assert list(self.d.keys()) == [2, ("Third", 0)]

    def test_dict(self):
        d = dict(self.d)  # type: MutableMapping[Any, Any]
        assert len(d.keys()) == 4
        assert d["FIRST"] == self.d["first"]
        assert d[2] == self.d[2]
        assert d[("Third", 0)] == self.d[("Third", 0)]
        assert d[1] == self.d[1]

    def test_eq_self(self):
        other = oci_dict(
            [("fIRst", 100), (2, None), (("Third", 0), (1, 2, 3)), (1, "AnB")]
        )  # type: oci_dict[Any, Any]
        assert self.d == other

        del other["first"]
        other["first"] = 100  # reorder

        assert self.d != other
        assert self.d == dict(other)
        assert dict(self.d) == other
        assert dict(self.d) == dict(other)

    def test_eq_ordered_dict(self):
        other = collections.OrderedDict(
            [("FIRST", 100), (2, None), (("Third", 0), (1, 2, 3)), (1, "AnB")]
        )
        assert self.d == other

        del other["FIRST"]
        other["FIRST"] = 100  # reorder

        assert self.d != other
        assert self.d == dict(other)
        assert dict(self.d) == other
        assert dict(self.d) == dict(other)

    def test_getitem_and_get(self):
        assert self.d["FiRST"] == 100
        assert self.d[2] is None
        assert self.d[("Third", 0)] == (1, 2, 3)
        with pytest.raises(KeyError):
            self.d[("third", 0)]  # inner elements are case sensitive

        assert self.d.get("FiRSt") == 100
        assert self.d.get(2) is None
        assert self.d.get(("Third", 0)) == (1, 2, 3)
        assert self.d.get(("third", 0), "NotFound") == "NotFound"
        assert self.d.get(123, 456) == 456

    def test_len(self):
        assert len(self.d) == 4

    def test_clear(self):
        self.d.clear()
        assert len(self.d) == 0

    def test_move_to_end(self):
        self.d.move_to_end("FIRST", last=True)  # case insensitive
        assert list(self.d.keys()) == [2, ("Third", 0), 1, "FIRST"]

        self.d.move_to_end(("Third", 0), last=False)
        assert list(self.d.keys()) == [("Third", 0), 2, 1, "FIRST"]

    def test_fromkeys(self):
        d = oci_dict.fromkeys(["a", "B", "thiRD", ("M", "n"), 3], True)
        assert list(d.keys()) == ["A", "B", "THIRD", ("M", "n"), 3]
        assert d["A"]
        assert d["B"]
        assert d["Third"]
        assert d[("M", "n")]
        assert d[3]

    def test_copy(self):
        d = self.d.copy()
        assert d == self.d
        d.move_to_end("first")
        assert d != self.d

    def test_keys_and_reversed(self):
        expected = ["FIRST", 2, ("Third", 0), 1]
        assert list(self.d.keys()) == expected
        assert list(reversed(self.d)) == list(reversed(expected))

    def test_values(self):
        assert list(self.d.values()) == [100, None, (1, 2, 3), "AnB"]

    def test_items(self):
        ks, vs = [], []
        for k, v in self.d.items():
            ks.append(k)
            vs.append(v)
        assert ks == list(self.d.keys())
        assert vs == list(self.d.values())

    def test_update(self):
        other = {"FIRST": 9, "seCond": 2, 2: True}
        self.d.update(other)
        assert self.d["fiRSt"] == 9
        assert self.d["Second"] == 2
        assert self.d[2] is True
        assert self.d[1] == "AnB"

    def test_pop(self):
        assert self.d.pop("fiRSt") == 100
        assert self.d.pop(2) is None
        with pytest.raises(KeyError):
            self.d.pop("first")
        with pytest.raises(KeyError):
            self.d.pop(100)
        assert self.d.pop(("Third", 0)) == (1, 2, 3)
        assert len(self.d) == 1

    def test_pop_with_default(self):
        assert self.d.pop("fiRSt", 9) == 100
        assert self.d.pop(2, default=9) is None
        assert self.d.pop("first", 12345) == 12345
        assert self.d.pop(100, default=12345) == 12345
        assert len(self.d) == 2

    def test_popitem(self):
        assert self.d.popitem(last=True) == (1, "AnB")
        assert self.d.popitem(last=False) == ("FIRST", 100)
        assert len(self.d) == 2


class TestOrderedTupleOrderInsensitiveDict(unittest.TestCase):
    """Unit test of `OrderedTupleOrderInsensitiveDict`."""

    def setUp(self):
        self.d = toi_dict()  # type: toi_dict[Any, Any]
        self.d[1, 1, 1, 0] = 100
        self.d[300] = None
        self.d[(2, 1), (4, 2), (2, 3)] = (1, 2, 3)  # inner elements are not ordered
        self.d[4, 3, 2, 1] = "AnB"

    def test_init_by_list(self):
        d = toi_dict(
            [
                ((0, 1, 1, 1), 100),
                (300, None),
                (((2, 3), (2, 1), (4, 2)), (1, 2, 3)),
                ((1, 3, 2, 4), "AnB"),
            ]
        )  # type: toi_dict[Any, Any]
        assert self.d == d
        assert d[1, 0, 1, 1] == 100
        assert d[0, 1, 1, 1] == 100
        assert d[300] is None
        assert d[(2, 1), (2, 3), (4, 2)] == (1, 2, 3)
        assert d[(4, 2), (2, 1), (2, 3)] == (1, 2, 3)
        assert d[1, 2, 3, 4] == "AnB"
        assert d[4, 2, 1, 3] == "AnB"
        assert list(d.keys()) == [
            (0, 1, 1, 1),
            300,
            ((2, 1), (2, 3), (4, 2)),
            (1, 2, 3, 4),
        ]

        with pytest.raises(KeyError):
            d[(2, 4), (1, 2), (2, 3)]

    def test_init_by_keywords(self):
        d = toi_dict(first=3, second=None)  # type: toi_dict[Any, Any]
        assert d["first"] == 3
        assert d["second"] is None

    def test_contains(self):
        assert (0, 1, 1, 1) in self.d
        assert (1, 0, 1, 1) in self.d
        assert (0, 0, 0, 0) not in self.d
        assert (1, 1, 1, 1) not in self.d

        assert None not in self.d
        assert 10 not in self.d

        assert ((2, 1), (2, 3), (4, 2)) in self.d
        assert ((1, 2), (2, 3), (4, 2)) not in self.d
        assert ((1, 2), (2, 3), (2, 4)) not in self.d

        # a bit tricky...
        assert 300 in self.d
        assert (300,) not in self.d
        assert (1, 2, 3, 4) in self.d

    def test_delitem(self):
        del self.d[0, 1, 1, 1]
        del self.d[300]
        del self.d[(4, 2), (2, 1), (2, 3)]
        assert list(self.d.keys()) == [(1, 2, 3, 4)]

    def test_dict(self):
        d = dict(self.d)  # type: MutableMapping[Any, Any]
        assert len(d.keys()) == 4
        for k in d.keys():
            assert d[k] == self.d[k]

    def test_eq_self(self):
        other = toi_dict(
            [
                ((0, 1, 1, 1), 100),
                (300, None),
                (((2, 3), (2, 1), (4, 2)), (1, 2, 3)),
                ((1, 2, 3, 4), "AnB"),
            ]
        )  # type: toi_dict[Any, Any]
        assert self.d == other

        del other[1, 1, 0, 1]
        other[1, 0, 1, 1] = 100  # reorder

        assert self.d != other
        assert self.d == dict(other)
        assert dict(self.d) == other
        assert dict(self.d) == dict(other)

    def test_eq_ordered_dict(self):
        other = collections.OrderedDict(
            [
                ((0, 1, 1, 1), 100),
                (300, None),
                (((2, 1), (2, 3), (4, 2)), (1, 2, 3)),
                ((1, 2, 3, 4), "AnB"),
            ]
        )
        assert self.d == other

        del other[0, 1, 1, 1]
        other[0, 1, 1, 1] = 100  # reorder

        assert self.d != other
        assert self.d == dict(other)
        assert dict(self.d) == other
        assert dict(self.d) == dict(other)

    def test_getitem_and_get(self):
        assert self.d[1, 1, 1, 0] == 100
        assert self.d[0, 1, 1, 1] == 100
        assert self.d[300] is None
        assert self.d[(2, 3), (4, 2), (2, 1)] == (1, 2, 3)
        with pytest.raises(KeyError):
            self.d[(1, 2), (2, 3), (2, 4)]  # inner elements are order preserved

        assert self.d.get((1, 1, 0, 1)) == 100
        assert self.d.get(300) is None
        assert self.d.get((4, 3, 2, 1)) == "AnB"
        assert self.d.get((4, 3, 2, 1), default=True) == "AnB"
        assert self.d.get((4, 3, 2, 1), True) == "AnB"
        assert self.d.get((1, 2, 3, 5)) is None
        assert self.d.get((1, 2, 3, 5), default=True) is True
        assert self.d.get((1, 2, 3, 5), True) is True

        assert self.d[0, 1, 1, 1] == 100
        assert self.d[0, 1, 1, 1] == 100

    def test_len(self):
        assert len(self.d) == 4

    def test_clear(self):
        self.d.clear()
        assert len(self.d) == 0

    def test_move_to_end(self):
        self.d.move_to_end((1, 1, 1, 0), last=True)  # case insensitive
        assert list(self.d.keys()) == [
            300,
            ((2, 1), (2, 3), (4, 2)),
            (1, 2, 3, 4),
            (0, 1, 1, 1),
        ]

        self.d.move_to_end(((2, 3), (4, 2), (2, 1)), last=False)
        assert list(self.d.keys()) == [
            ((2, 1), (2, 3), (4, 2)),
            300,
            (1, 2, 3, 4),
            (0, 1, 1, 1),
        ]

    def test_fromkeys(self):
        d = toi_dict.fromkeys([(1, 0), 3, (-1, 1, 0), (3, 2, -3)], True)
        assert list(d.keys()) == [(0, 1), 3, (-1, 0, 1), (-3, 2, 3)]
        assert d[1, 0]
        assert d[3]
        assert d[0, 1, -1]
        assert d[2, 3, -3]

    def test_copy(self):
        d = self.d.copy()
        assert d == self.d
        d.move_to_end((1, 0, 1, 1))
        assert d != self.d

    def test_keys_and_reversed(self):
        expected = [(0, 1, 1, 1), 300, ((2, 1), (2, 3), (4, 2)), (1, 2, 3, 4)]
        assert list(self.d.keys()) == expected
        assert list(reversed(self.d)) == list(reversed(expected))

    def test_values(self):
        assert list(self.d.values()) == [100, None, (1, 2, 3), "AnB"]

    def test_items(self):
        ks, vs = [], []
        for k, v in self.d.items():
            ks.append(k)
            vs.append(v)
        assert ks == list(self.d.keys())
        assert vs == list(self.d.values())

    def test_update(self):
        other = {(1, 0, 1, 1): 9, 300: 2, (3, 2, 1): True}
        self.d.update(other)
        assert self.d[1, 1, 0, 1] == 9
        assert self.d[300] == 2
        assert self.d[2, 3, 1] is True
        assert self.d[(2, 3), (2, 1), (4, 2)] == (1, 2, 3)
        assert self.d[1, 4, 2, 3] == "AnB"
        assert len(self.d) == 5

    def test_pop(self):
        assert self.d.pop((1, 0, 1, 1)) == 100
        assert self.d.pop(300) is None
        with pytest.raises(KeyError):
            self.d.pop((1, 1, 1, 0))
        with pytest.raises(KeyError):
            self.d.pop(300)
        assert self.d.pop((1, 2, 4, 3)) == "AnB"
        assert len(self.d) == 1

    def test_pop_with_default(self):
        assert self.d.pop((1, 0, 1, 1), 9) == 100
        assert self.d.pop(300, default=9) is None
        assert self.d.pop((0, 1, 1, 1), 12345) == 12345
        assert self.d.pop((1, 0, 1, 1), default=12345) == 12345
        assert len(self.d) == 2

    def test_popitem(self):
        assert self.d.popitem(last=True) == ((1, 2, 3, 4), "AnB")
        assert self.d.popitem(last=False) == ((0, 1, 1, 1), 100)
        assert len(self.d) == 2
