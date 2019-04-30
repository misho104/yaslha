"""Sample codes of yaslha, serves also as test codes.

This example contains basic read/write of SLHA data.
"""

import logging
import unittest

from nose.tools import assert_raises, eq_, ok_, raises  # noqa: F401

from yaslha.parser import SLHAParser

logger = logging.getLogger("test_info")


class TestExampleBasic(unittest.TestCase):
    """Basic read/write of SLHA data."""

    slha_string = """
# SUSY Les Houches Accord 1.0 - example input file
# Snowmass point 1a
Block MODSEL  # Select model
     1    1   # sugra
Block SMINPUTS   # Standard Model inputs
     3      0.1172  # alpha_s(MZ) SM msbar
     5      4.25    # Mb(mb) SM msbar
     6    174.3     # Mtop(pole)
Block MINPAR  # SUSY breaking input parameters
     3     10.0     # tanb
     4      1.0     # sign(mu)
     1    100.0     # m0
     2    250.0     # m12
     5   -100.0     # A0
"""

    def setUp(self):
        parser = SLHAParser()
        self.slha = parser.parse(self.slha_string)

    def test_read_1(self):
        # simply read the data from Block
        eq_(self.slha["MODSEL", 1], 1)
        eq_(self.slha["SMINPUTS", 3], 0.1172)
        eq_(self.slha["MINPAR", 3], 10.0)

        # block name is case-insensitive
        eq_(self.slha["SMinputs", 6], 174.3)

    def test_read_2(self):
        # read the data in another syntax
        eq_(self.slha["MODSEL"][1], 1)
        eq_(self.slha["SMinputs"][6], 174.3)

        # these are equivalent to, for example,
        minpar_block = self.slha["minpar"]
        eq_(minpar_block[3], 10.0)
        eq_(minpar_block[4], 1.0)

    def test_update(self):
        # update/add data
        self.slha["SMinputs", 6] = 172.3
        self.slha["SMINPUTS", 11] = 0.511e-3

        eq_(self.slha["SMINPUTS", 6], 172.3)
        eq_(self.slha["SMINPUTS"][11], 0.511e-3)

        # a bit more technical operation
        minpar_block = self.slha["minpar"]
        minpar_block[3] = 40.0
        minpar_block[6] = 123.456

        eq_(self.slha["minpar", 3], 40.0)
        eq_(self.slha["minpar", 6], 123.456)

    def test_add_block(self):
        # To create a new block
        self.slha["extpar", 1] = 100.12
        eq_(self.slha["EXTPAR", 1], 100.12)

        # This doesn't work because self.slha["new"] is not yet defined (thus KeyError).
        with assert_raises(KeyError):
            self.slha["new"][1] = 100.12

    def test_delete(self):
        # you can remove the data
        del self.slha["SMinputs", 6]
        del self.slha["minpar"][3]

        with assert_raises(KeyError):
            self.slha["minpar", 3]

        with assert_raises(KeyError):
            self.slha["sminputs"][6]

        # block structure is not removed even if all the data are removed
        del self.slha["minpar", 1]
        self.slha["minpar"][1] = 2
        eq_(self.slha["minpar", 1], 2)


# cspell:ignore modsel sugra tanb sminputs msbar mtop
