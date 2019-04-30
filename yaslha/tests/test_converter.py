"""Tests for convert sub-commmand."""

import logging
import pathlib
import re
import traceback
import unittest

import coloredlogs
from click.testing import CliRunner
from nose.tools import eq_, ok_, raises  # noqa: F401

import yaslha.dumper
from yaslha.script import convert

logger = logging.getLogger("test_info")


def check_and_separate_output(result):
    """Separate STDERR-like lines from STDOUT text."""
    if result.exit_code != 0:
        traceback.print_tb(result.exc_info[2])
        print(result.exc_info[1])
    eq_(result.exit_code, 0)

    # separate logging lines to STDERR
    re_logline = re.compile(r"(yaslha\.\w+:)? (CRITICAL|ERROR|WARNING|DEBUG|INFO)[: ]")
    stdout = []
    stderr = []
    for i in result.output.splitlines():
        if re_logline.match(i):
            stderr.append(i)
        else:
            stdout.append(i)
    return stdout, stderr


def compare_lines(a, b):
    """Compare two texts line by line."""
    if isinstance(a, str):
        return compare_lines(a.splitlines(), b)
    if isinstance(b, str):
        return compare_lines(a, b.splitlines())
    a.append("*END_OF_TEXT*")
    b.append("*END_OF_TEXT*")
    na, nb = len(a), len(b)
    for i, ta in enumerate(a):
        eq_(ta, b[i] if i < nb else "")
    eq_(na, nb)


class TestConverter(unittest.TestCase):
    """Test class for converter sub-command."""

    def setUp(self):
        coloredlogs.set_level(40)
        self.data_dir = pathlib.Path(__file__).parent / "data"
        self.inputs = [
            str(path) for path in self.data_dir.glob("*.*") if path.is_file()
        ]
        self.runner = CliRunner()

    def test_idempotence(self):
        for input_file in self.inputs:
            for block_order in yaslha.dumper.BlocksOrder:
                for value_order in yaslha.dumper.ValuesOrder:
                    for comment in yaslha.dumper.CommentsPreserve:
                        args = [
                            "--input-type=SLHA",
                            "--output-type=SLHA",
                            "--blocks=" + block_order.name,
                            "--values=" + value_order.name,
                            "--comments=" + comment.name,
                        ]
                        result1 = self.runner.invoke(convert, args + [input_file])
                        result1_output, result1_stderr = check_and_separate_output(
                            result1
                        )
                        result2 = self.runner.invoke(
                            convert, args, input="\n".join(result1_output)
                        )
                        result2_output, result2_stderr = check_and_separate_output(
                            result2
                        )
                        compare_lines(result1_output, result2_output)
