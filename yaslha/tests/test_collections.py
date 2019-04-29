"""Unit test of `_collections` module."""

import collections
import logging
import unittest
from typing import Any, MutableMapping

from nose.tools import assert_raises, eq_, ok_  # noqa: F401

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
        eq_(d["A"], 10)
        eq_(d["b"], 30)
        eq_(d["B"], 30)
        eq_(d[None], "AnB")
        eq_(d[1], "300aBC")
        eq_(list(d.keys()), ["A", "B", None, 1])

    def test_init_by_keywords(self):
        d = oci_dict(
            FiRST=3, SeCoND=None, third=(1, 2, 3), lAST="AnB"
        )  # type: oci_dict[Any, Any]
        eq_(d["FIRST"], 3)
        eq_(d["second"], None)
        eq_(d["third"], (1, 2, 3))
        eq_(d["last"], "AnB")

    def test_contains(self):
        ok_("first" in self.d)
        ok_("FIRst" in self.d)
        ok_("_first" not in self.d)

        ok_(None not in self.d)
        ok_(2 in self.d)
        ok_(3 not in self.d)

        ok_(("Third", 0) in self.d)
        ok_(("third", 0) not in self.d)

    def test_delitem(self):
        del self.d["FIrST"]
        del self.d[1]
        eq_(list(self.d.keys()), [2, ("Third", 0)])

    def test_dict(self):
        d = dict(self.d)  # type: MutableMapping[Any, Any]
        eq_(len(d.keys()), 4)
        eq_(d["FIRST"], self.d["first"])
        eq_(d[2], self.d[2])
        eq_(d[("Third", 0)], self.d[("Third", 0)])
        eq_(d[1], self.d[1])

    def test_eq_self(self):
        other = oci_dict(
            [("fIRst", 100), (2, None), (("Third", 0), (1, 2, 3)), (1, "AnB")]
        )  # type: oci_dict[Any, Any]
        ok_(self.d == other)

        del other["first"]
        other["first"] = 100  # reorder

        ok_(self.d != other)
        ok_(self.d == dict(other))
        ok_(dict(self.d) == other)
        ok_(dict(self.d) == dict(other))

    def test_eq_ordered_dict(self):
        other = collections.OrderedDict(
            [("FIRST", 100), (2, None), (("Third", 0), (1, 2, 3)), (1, "AnB")]
        )
        ok_(self.d == other)

        del other["FIRST"]
        other["FIRST"] = 100  # reorder

        ok_(self.d != other)
        ok_(self.d == dict(other))
        ok_(dict(self.d) == other)
        ok_(dict(self.d) == dict(other))

    def test_getitem_and_get(self):
        eq_(self.d["FiRST"], 100)
        eq_(self.d[2], None)
        eq_(self.d[("Third", 0)], (1, 2, 3))
        with assert_raises(KeyError):
            self.d[("third", 0)]  # inner elements are case sensitive

        eq_(self.d.get("FiRSt"), 100)
        eq_(self.d.get(2), None)
        eq_(self.d.get(("Third", 0)), (1, 2, 3))
        eq_(self.d.get(("third", 0), "NotFound"), "NotFound")
        eq_(self.d.get(123, 456), 456)

    def test_len(self):
        eq_(len(self.d), 4)

    def test_clear(self):
        self.d.clear()
        eq_(len(self.d), 0)

    def test_move_to_end(self):
        self.d.move_to_end("FIRST", last=True)  # case insensitive
        eq_(list(self.d.keys()), [2, ("Third", 0), 1, "FIRST"])

        self.d.move_to_end(("Third", 0), last=False)
        eq_(list(self.d.keys()), [("Third", 0), 2, 1, "FIRST"])

    def test_fromkeys(self):
        d = oci_dict.fromkeys(["a", "B", "thiRD", ("M", "n"), 3], True)
        eq_(list(d.keys()), ["A", "B", "THIRD", ("M", "n"), 3])
        eq_(d["A"], True)
        eq_(d["B"], True)
        eq_(d["Third"], True)
        eq_(d[("M", "n")], True)
        eq_(d[3], True)

    def test_copy(self):
        d = self.d.copy()
        ok_(d == self.d)
        d.move_to_end("first")
        ok_(d != self.d)

    def test_keys_and_reversed(self):
        expected = ["FIRST", 2, ("Third", 0), 1]
        eq_(list(self.d.keys()), expected)
        eq_(list(reversed(self.d)), list(reversed(expected)))

    def test_values(self):
        eq_(list(self.d.values()), [100, None, (1, 2, 3), "AnB"])

    def test_items(self):
        ks, vs = [], []
        for k, v in self.d.items():
            ks.append(k)
            vs.append(v)
        eq_(ks, list(self.d.keys()))
        eq_(vs, list(self.d.values()))

    def test_update(self):
        other = {"FIRST": 9, "seCond": 2, 2: True}
        self.d.update(other)
        eq_(self.d["fiRSt"], 9)
        eq_(self.d["Second"], 2)
        eq_(self.d[2], True)
        eq_(self.d[1], "AnB")

    def test_pop(self):
        eq_(self.d.pop("fiRSt"), 100)
        eq_(self.d.pop(2), None)
        with assert_raises(KeyError):
            self.d.pop("first")
        with assert_raises(KeyError):
            self.d.pop(100)
        eq_(self.d.pop(("Third", 0)), (1, 2, 3))
        eq_(len(self.d), 1)

    def test_pop_with_default(self):
        eq_(self.d.pop("fiRSt", 9), 100)
        eq_(self.d.pop(2, default=9), None)
        eq_(self.d.pop("first", 12345), 12345)
        eq_(self.d.pop(100, default=12345), 12345)
        eq_(len(self.d), 2)

    def test_popitem(self):
        eq_(self.d.popitem(last=True), (1, "AnB"))
        eq_(self.d.popitem(last=False), ("FIRST", 100))
        eq_(len(self.d), 2)


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
        ok_(self.d, d)
        eq_(d[1, 0, 1, 1], 100)
        eq_(d[0, 1, 1, 1], 100)
        eq_(d[300], None)
        eq_(d[(2, 1), (2, 3), (4, 2)], (1, 2, 3))
        eq_(d[(4, 2), (2, 1), (2, 3)], (1, 2, 3))
        eq_(d[1, 2, 3, 4], "AnB")
        eq_(d[4, 2, 1, 3], "AnB")
        eq_(list(d.keys()), [(0, 1, 1, 1), 300, ((2, 1), (2, 3), (4, 2)), (1, 2, 3, 4)])

        with assert_raises(KeyError):
            d[(2, 4), (1, 2), (2, 3)]

    def test_init_by_keywords(self):
        d = toi_dict(first=3, second=None)  # type: toi_dict[Any, Any]
        eq_(d["first"], 3)
        eq_(d["second"], None)

    def test_contains(self):
        ok_((0, 1, 1, 1) in self.d)
        ok_((1, 0, 1, 1) in self.d)
        ok_((0, 0, 0, 0) not in self.d)
        ok_((1, 1, 1, 1) not in self.d)

        ok_(None not in self.d)
        ok_(10 not in self.d)

        ok_(((2, 1), (2, 3), (4, 2)) in self.d)
        ok_(((1, 2), (2, 3), (4, 2)) not in self.d)
        ok_(((1, 2), (2, 3), (2, 4)) not in self.d)

        # a bit tricky...
        ok_(300 in self.d)
        ok_((300,) not in self.d)
        ok_((1, 2, 3, 4) in self.d)

    def test_delitem(self):
        del self.d[0, 1, 1, 1]
        del self.d[300]
        del self.d[(4, 2), (2, 1), (2, 3)]
        eq_(list(self.d.keys()), [(1, 2, 3, 4)])

    def test_dict(self):
        d = dict(self.d)  # type: MutableMapping[Any, Any]
        eq_(len(d.keys()), 4)
        for k in d.keys():
            eq_(d[k], self.d[k])

    def test_eq_self(self):
        other = toi_dict(
            [
                ((0, 1, 1, 1), 100),
                (300, None),
                (((2, 3), (2, 1), (4, 2)), (1, 2, 3)),
                ((1, 2, 3, 4), "AnB"),
            ]
        )  # type: toi_dict[Any, Any]
        ok_(self.d == other)

        del other[1, 1, 0, 1]
        other[1, 0, 1, 1] = 100  # reorder

        ok_(self.d != other)
        ok_(self.d == dict(other))
        ok_(dict(self.d) == other)
        ok_(dict(self.d) == dict(other))

    def test_eq_ordered_dict(self):
        other = collections.OrderedDict(
            [
                ((0, 1, 1, 1), 100),
                (300, None),
                (((2, 1), (2, 3), (4, 2)), (1, 2, 3)),
                ((1, 2, 3, 4), "AnB"),
            ]
        )
        ok_(self.d == other)

        del other[0, 1, 1, 1]
        other[0, 1, 1, 1] = 100  # reorder

        ok_(self.d != other)
        ok_(self.d == dict(other))
        ok_(dict(self.d) == other)
        ok_(dict(self.d) == dict(other))

    def test_getitem_and_get(self):
        eq_(self.d[1, 1, 1, 0], 100)
        eq_(self.d[0, 1, 1, 1], 100)
        eq_(self.d[300], None)
        eq_(self.d[(2, 3), (4, 2), (2, 1)], (1, 2, 3))
        with assert_raises(KeyError):
            self.d[(1, 2), (2, 3), (2, 4)]  # inner elements are order preserved

        eq_(self.d.get((1, 1, 0, 1)), 100)
        eq_(self.d.get(300), None)
        eq_(self.d.get((4, 3, 2, 1)), "AnB")
        eq_(self.d.get((4, 3, 2, 1), default=True), "AnB")
        eq_(self.d.get((4, 3, 2, 1), True), "AnB")
        eq_(self.d.get((1, 2, 3, 5)), None)
        eq_(self.d.get((1, 2, 3, 5), default=True), True)
        eq_(self.d.get((1, 2, 3, 5), True), True)

        eq_(self.d[0, 1, 1, 1], 100)
        eq_(self.d[0, 1, 1, 1], 100)

    def test_len(self):
        eq_(len(self.d), 4)

    def test_clear(self):
        self.d.clear()
        eq_(len(self.d), 0)

    def test_move_to_end(self):
        self.d.move_to_end((1, 1, 1, 0), last=True)  # case insensitive
        eq_(
            list(self.d.keys()),
            [300, ((2, 1), (2, 3), (4, 2)), (1, 2, 3, 4), (0, 1, 1, 1)],
        )

        self.d.move_to_end(((2, 3), (4, 2), (2, 1)), last=False)
        eq_(
            list(self.d.keys()),
            [((2, 1), (2, 3), (4, 2)), 300, (1, 2, 3, 4), (0, 1, 1, 1)],
        )

    def test_fromkeys(self):
        d = toi_dict.fromkeys([(1, 0), 3, (-1, 1, 0), (3, 2, -3)], True)
        eq_(list(d.keys()), [(0, 1), 3, (-1, 0, 1), (-3, 2, 3)])
        eq_(d[1, 0], True)
        eq_(d[3], True)
        eq_(d[0, 1, -1], True)
        eq_(d[2, 3, -3], True)

    def test_copy(self):
        d = self.d.copy()
        ok_(d == self.d)
        d.move_to_end((1, 0, 1, 1))
        ok_(d != self.d)

    def test_keys_and_reversed(self):
        expected = [(0, 1, 1, 1), 300, ((2, 1), (2, 3), (4, 2)), (1, 2, 3, 4)]
        eq_(list(self.d.keys()), expected)
        eq_(list(reversed(self.d)), list(reversed(expected)))

    def test_values(self):
        eq_(list(self.d.values()), [100, None, (1, 2, 3), "AnB"])

    def test_items(self):
        ks, vs = [], []
        for k, v in self.d.items():
            ks.append(k)
            vs.append(v)
        eq_(ks, list(self.d.keys()))
        eq_(vs, list(self.d.values()))

    def test_update(self):
        other = {(1, 0, 1, 1): 9, 300: 2, (3, 2, 1): True}
        self.d.update(other)
        eq_(self.d[1, 1, 0, 1], 9)
        eq_(self.d[300], 2)
        eq_(self.d[2, 3, 1], True)
        eq_(self.d[(2, 3), (2, 1), (4, 2)], (1, 2, 3))
        eq_(self.d[1, 4, 2, 3], "AnB")
        eq_(len(self.d), 5)

    def test_pop(self):
        eq_(self.d.pop((1, 0, 1, 1)), 100)
        eq_(self.d.pop(300), None)
        with assert_raises(KeyError):
            self.d.pop((1, 1, 1, 0))
        with assert_raises(KeyError):
            self.d.pop(300)
        eq_(self.d.pop((1, 2, 4, 3)), "AnB")
        eq_(len(self.d), 1)

    def test_pop_with_default(self):
        eq_(self.d.pop((1, 0, 1, 1), 9), 100)
        eq_(self.d.pop(300, default=9), None)
        eq_(self.d.pop((0, 1, 1, 1), 12345), 12345)
        eq_(self.d.pop((1, 0, 1, 1), default=12345), 12345)
        eq_(len(self.d), 2)

    def test_popitem(self):
        eq_(self.d.popitem(last=True), ((1, 2, 3, 4), "AnB"))
        eq_(self.d.popitem(last=False), ((0, 1, 1, 1), 100))
        eq_(len(self.d), 2)
