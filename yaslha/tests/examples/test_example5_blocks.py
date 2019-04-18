"""Sample codes of yaslha, serves also as test codes.

This example contains block-wise operations.
"""

import copy
import logging
import unittest

from nose.tools import assert_raises, eq_, ok_, raises  # noqa: F401

from yaslha.block import Block, Decay
from yaslha.parser import SLHAParser

logger = logging.getLogger("test_info")


class TestExampleBlockOperation(unittest.TestCase):
    """Block-wise operation for SLHA data."""

    slha_string = """
Block SPINFO         # Program information
     1   SOFTSUSY    # spectrum calculator
     2   1.8.4       # version number
Block MODSEL  # Select model
     1    1   # sugra
Block alpha   # Effective Higgs mixing parameter
          -1.13716828e-01   # alpha
Block gauge Q= 4.64649125e+02
     1     3.60872342e-01   # g'(Q)MSSM drbar
     2     6.46479280e-01   # g(Q)MSSM drbar
     3     1.09623002e+00   # g3(Q)MSSM drbar
Block au Q= 4.64649125e+02
  3  3    -5.04995511e+02   # At(Q)MSSM drbar

DECAY   1000023     1.95831641E-02   # chi_20
     5.00000000E-01    2    -2000011        11
     4.00000000E-01    2    -2000013        13
     1.00000000E-01    3     1000022         1        -1

DECAY   999     1.00E-02    # data for testing
     0.10    2    123      4                 # 0.0010
     0.15    2    123      5                 # 0.0015
     0.30    2    123   -123                 # 0.0030
     0.40    3    123    123    123          # 0.0040
     0.05    4      1      2      3      4   # 0.0005
"""

    def setUp(self):
        parser = SLHAParser()
        self.slha = parser.parse(self.slha_string)

    def test_basic_block_operation_1(self):
        gauge = self.slha["gauge"]

        # now one can handle this block itself
        gauge[1] = 0.1
        gauge[2] = 0.4
        gauge.q = 100.123
        del gauge[3]

        # the original SLHA data **is** affected.
        eq_(self.slha["gauge"][1], 0.1)
        eq_(self.slha["gauge", 2], 0.4)
        eq_(self.slha["gauge"].q, 100.123)
        with assert_raises(KeyError):
            self.slha["gauge", 3]

    def test_basic_block_operation_2(self):
        # if you want to unlink the block from SLHA, you must use deep-copy.
        gauge_copied = copy.deepcopy(self.slha["Gauge"])

        eq_(gauge_copied[1], 3.60872342e-01)
        eq_(gauge_copied.q, 4.64649125e02)  # the data and q value are copied

        # changing the contents of the new block
        gauge_copied[2] = -0.2
        del gauge_copied[3]

        # the new block is modified
        eq_(gauge_copied[2], -0.2)
        with assert_raises(KeyError):
            gauge_copied[3]

        # the original SLHA data is not modified.
        eq_(self.slha["gauge", 1], 3.60872342e-01)
        eq_(self.slha["gauge", 2], 6.46479280e-01)
        eq_(self.slha["gauge", 3], 1.09623002e00)

        # you may replace the block
        self.slha["gauge"] = gauge_copied
        eq_(self.slha["gauge", 1], 3.60872342e-01)
        eq_(self.slha["gauge", 2], -0.2)
        eq_(self.slha.get("gauge", 3), None)

    def test_slha_iterators_blocks(self):
        # iterator only for ordinal blocks
        expected = ["spinfo", "modsel", "alpha", "gauge", "au"]
        for name in self.slha.blocks:
            ok_(name.lower() in expected)
            expected.remove(name.lower())
        ok_(len(expected) == 0)

    def test_slha_iterators_decays(self):
        # iterator only for decay blocks
        expected = [1000023, 999]
        for pid in self.slha.decays:
            ok_(pid in expected)
            expected.remove(pid)
        ok_(len(expected) == 0)

    def test_add_block(self):
        # a new block
        new_block = Block("")
        new_block.q = 123.456
        new_block[3] = 10.05

        # assign a new block to SLHA object
        self.slha["NEWBLOCK"] = new_block

        eq_(self.slha["newblock", 3], 10.05)
        eq_(self.slha["newblock"].q, 123.456)

        # the block name is modified accordingly
        eq_(self.slha["NewBlock"].name.lower(), "newblock")

    def test_add_block_2(self):
        # another method to add block
        new_block = Block("newblock")
        new_block.q = 123.456
        new_block[3] = 10.05

        self.slha.add_block(new_block)
        eq_(self.slha["newblock", 3], 10.05)
        eq_(self.slha["newblock"].q, 123.456)

    def test_add_decay_block(self):
        # a new block
        new_decay = Decay(789)
        new_decay.set_partial_width(123, 123, 0.01)
        new_decay.set_partial_width(123, -123, 0.02)
        new_decay.set_partial_width(4, 3, 2, 0.01)

        # assign a new block to SLHA object
        self.slha[789] = new_decay

        eq_(self.slha[789].br(123, 123), 0.25)
        eq_(self.slha[789].partial_width(123, -123), 0.02)
        eq_(self.slha[789].width, 0.04)

    def test_delete_block(self):
        # remove a block
        del self.slha["modsel"]

        with assert_raises(KeyError):
            self.slha["modsel"]

        # remove a decay block
        del self.slha[999]
        eq_(list(self.slha.decays.keys()), [1000023])


# cspell:ignore softsusy modsel sminputs msbar drbar mgut mssm higgs hmix sugra tanb
