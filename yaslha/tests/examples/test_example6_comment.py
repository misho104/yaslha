"""Sample codes of yaslha, serves also as test codes.

This example contains comment handlings.
"""

import logging
import unittest

from nose.tools import assert_raises, eq_, ok_, raises  # noqa: F401

from yaslha.parser import SLHAParser

logger = logging.getLogger("test_info")


class TestExampleComment(unittest.TestCase):
    """Advanced read/write of SLHA data."""

    slha_string = """
# SLHA 1.0
# calculator
Block SPINFO         # Program information
     1   SOFTSUSY    # name
     2   1.8.4       # version number
# Input parameters
Block MODSEL  # Select model
     1    1   # sugra
Block MINPAR  # SUSY breaking input parameters
# comment between lines (1)
     1    1.00000000e+02   # m0(MGUT) MSSM drbar
     2    2.50000000e+02   # m12(MGUT) MSSM drbar
# comment between lines (2)
     3    1.00000000e+01   # tanb(MZ) MSSM drbar
     4    1.00000000e+00   # sign(mu(MGUT)) MSSM drbar
     5   -1.00000000e+02   # A0(MGUT) MSSM drbar
# comment after minpar
Block MASS  # Mass spectrum
# PDG code     mass               particle
   1000001     5.73103437e+02   # ~d_L
   1000002     5.67658152e+02   # ~u_L
   1000003     5.73029886e+02   # ~s_L
   1000004     5.67583798e+02   # ~c_L
   1000005     5.15617364e+02   # ~b_1
   1000006     3.96457239e+02   # ~t_1
Block hmix Q= 4.64649125e+02
     1     3.58660361e+02
     2     9.75139550e+00
     3     2.44923506e+02
     4     1.69697051e+04
#
#         PDG        Width
DECAY   1000023     1.95831641E-02   # chi_20
#    BR                NDA      ID1      ID2
     3.38444885E-02    2    -2000011        11   # BR(chi_20 -> ~e_R+ e- )
     3.38444885E-02    2     2000011       -11   # BR(chi_20 -> ~e_R- e+ )
     3.50457690E-02    2    -2000013        13   # BR(chi_20 -> ~mu_R+ mu- )
     3.50457690E-02    2     2000013       -13   # BR(chi_20 -> ~mu_R- mu+ )
     4.29284412E-01    2    -1000015        15   # BR(chi_20 -> ~tau_1+ tau- )
     4.29284412E-01    2     1000015       -15   # BR(chi_20 -> ~tau_1- tau+ )
     2.07507330E-06    2     1000022        22   # BR(chi_20 -> chi_10 photon )
#    BR                NDA      ID1      ID2       ID3
     1.75499602E-04    3     1000022         2        -2   # BR(chi_20 -> chi_10 u u )
     1.75229451E-04    3     1000022         4        -4   # BR(chi_20 -> chi_10 c c )
     2.33949042E-04    3     1000022         1        -1   # BR(chi_20 -> chi_10 d d )
#comment at SLHA-tail
"""

    def setUp(self):
        parser = SLHAParser()
        self.slha = parser.parse(self.slha_string)

    def test_read_1(self):
        # simple examples of pre-head, head, and line comments

        # pre-head comment is always List[str]
        eq_(self.slha["modsel"].comment.pre["head"], ["# Input parameters"])
        eq_(self.slha["spinfo"].comment.pre["head"], ["# SLHA 1.0", "# calculator"])

        # head comment is always str
        eq_(self.slha["modsel"].comment["head"], "Select model")
        eq_(self.slha["spinfo"].comment["head"], "Program information")

        # line-tail comment depends on block type
        eq_(self.slha["modsel"].comment[1], "sugra")  # str for ordinary block
        eq_(self.slha["mass"].comment[1000001], "~d_L")
        eq_(self.slha["spinfo"].comment[1], ["name"])  # List[str] for INFO blocks
        eq_(self.slha["spinfo"].comment[2], ["version number"])

        # another method to access
        modsel = self.slha["modsel"]
        eq_(modsel.comment.pre["head"], ["# Input parameters"])
        eq_(modsel.comment["head"], "Select model")
        eq_(modsel.comment[1], "sugra")

        # comments between lines are recognized as "pre" comments of the next lines.
        minpar = self.slha["minpar"]
        eq_(minpar.comment.pre[1], ["# comment between lines (1)"])  # always List[str]
        eq_(minpar.comment.pre[3], ["# comment between lines (2)"])

        # comments after block are recognized as pre-block comments of the next blocks.
        eq_(self.slha["mass"].comment.pre["head"], ["# comment after minpar"])

        # the comment at the end of file is specially treated
        eq_(self.slha.tail_comment, ["#comment at SLHA-tail"])  # always List[str]

        # empty string (or empty list) is returned if comment does not exist.
        eq_(self.slha["hmix"].comment.pre["head"], [])
        eq_(self.slha["hmix"].comment["head"], "")
        eq_(self.slha["hmix"].comment.pre[1], [])
        eq_(self.slha["hmix"].comment[1], "")

    def test_read_2(self):
        # for decay blocks
        eq_(self.slha[1000023].comment.pre["head"], ["#", "#         PDG        Width"])
        eq_(
            self.slha[1000023].comment.pre[11, -2000011],
            ["#    BR                NDA      ID1      ID2"],
        )
        eq_(self.slha[1000023].comment[11, -2000011], "BR(chi_20 -> ~e_R+ e- )")

    def test_update(self):
        modsel = self.slha["modsel"]
        # line comments are a string.
        modsel.comment["head"] = "new head comment"
        modsel.comment[1] = "new comment 2"
        eq_(self.slha["modsel"].comment["head"], "new head comment")
        eq_(self.slha["modsel"].comment[1], "new comment 2")

        # pre-line comments are a list of string.
        modsel.comment.pre["head"] = ["new pre-head comment"]
        modsel.comment.pre[1] = ["new comment 1"]
        eq_(self.slha["modsel"].comment.pre["head"], ["new pre-head comment"])
        eq_(self.slha["modsel"].comment.pre[1], ["new comment 1"])

        # for INFO blocks, line comments are a list of string.
        eq_(self.slha["spinfo"].comment[1], ["name"])
        eq_(self.slha["spinfo"].comment[2], ["version number"])
        self.slha["spinfo"].comment[1] = ["new comment 1"]
        self.slha["spinfo"].comment[2] = ["new comment 2"]
        eq_(self.slha["spinfo"].comment[1], ["new comment 1"])
        eq_(self.slha["spinfo"].comment[2], ["new comment 2"])

        # add comments
        self.slha["minpar", 6] = 0.5
        self.slha["minpar", 7] = 0.1
        self.slha["minpar"].comment.pre[6] = ["extra parameters"]
        self.slha["minpar"].comment[6] = "extra 1"
        self.slha["minpar"].comment[7] = "extra 2"
        eq_(self.slha["minpar"].comment.pre[6], ["extra parameters"])
        eq_(self.slha["minpar"].comment[6], "extra 1")
        eq_(self.slha["minpar"].comment[7], "extra 2")

        # one cannot assign comments to non-existing lines
        with assert_raises(KeyError):
            self.slha["minpar"].comment[8] = "non-existing line comment"
        with assert_raises(KeyError):
            self.slha["minpar"].comment.pre[8] = "non-existing pre-line comment"

    def test_delete(self):
        # comments can be removed by assigning None or empty values.
        self.slha["minpar"].comment[1] = None
        self.slha["minpar"].comment.pre[1] = None
        self.slha["minpar"].comment.pre["head"] = None
        self.slha["minpar"].comment["head"] = None

        eq_(self.slha["minpar"].comment[1], "")
        eq_(self.slha["minpar"].comment.pre[1], [])
        eq_(self.slha["minpar"].comment.pre["head"], [])
        eq_(self.slha["minpar"].comment["head"], "")  # note the different types


# cspell:ignore softsusy modsel sminputs msbar drbar mgut mssm higgs hmix sugra tanb
