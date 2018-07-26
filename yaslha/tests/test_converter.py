import logging
import pathlib
import traceback
import unittest
import warnings
from typing import List, Tuple, Union
from click.testing import CliRunner, Result
from nose.tools import raises, ok_, eq_  # noqa: F401

from yaslha.script import convert
import yaslha.dumper
logger = logging.getLogger('test_info')


def check_and_separate_output(result: Result)->Tuple[List[str], List[str]]:
    if result.exit_code != 0:
        traceback.print_tb(result.exc_info[2])
    eq_(result.exit_code, 0)

    stdout = []  # type: List[str]
    stderr = []  # type: List[str]
    for i in result.output.splitlines():
        if i.startswith('STDERR:::'):
            stderr.append(i[9:])
        else:
            stdout.append(i)
    return stdout, stderr


def compare_lines(a: Union[str, List[str]], b: Union[str, List[str]])->None:
    if isinstance(a, str):
        return compare_lines(a.splitlines(), b)
    if isinstance(b, str):
        return compare_lines(a, b.splitlines())
    a.append('*END_OF_TEXT*')
    b.append('*END_OF_TEXT*')
    na, nb = len(a), len(b)
    for i, ta in enumerate(a):
        eq_(ta, b[i] if i < nb else '')
    eq_(na, nb)


class TestAbsModelInitialization(unittest.TestCase):
    def setUp(self):
        self.data_dir = pathlib.Path(__file__).parent / 'data'
        self.inputs = [str(path) for path in self.data_dir.glob('*.*') if path.is_file()]
        self.runner = CliRunner()

        # Separate STDERR and STDOUT
        def formatwarning(message, category, filename, lineno, line=None):
            return ('STDERR:::%s: %s\n' % (category.__name__, message))
        warnings.formatwarning = formatwarning

    def test_idempotence(self):
        for input_file in self.inputs:
            for block_order in yaslha.dumper.BlocksOrder:
                for value_order in yaslha.dumper.ValuesOrder:
                    for comment in yaslha.dumper.CommentsPreserve:
                        args = ['--input-type=SLHA', '--output-type=SLHA',
                                '--blocks=' + block_order.name,
                                '--values=' + value_order.name,
                                '--comments=' + comment.name]
                        result1 = self.runner.invoke(convert, args + [input_file])
                        result1_output, result1_stderr = check_and_separate_output(result1)
                        result2 = self.runner.invoke(convert, args, input='\n'.join(result1_output))
                        result2_output, result2_stderr = check_and_separate_output(result2)
                        compare_lines(result1_output, result2_output)
