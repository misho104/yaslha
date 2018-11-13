import warnings
from typing import Optional, Type, List  # noqa: F401
from yaslha.utility import KeyType  # noqa: F401
import yaslha.line  # noqa: F401


def formatwarning(message, category, filename, lineno, line=None):
    # type: (str, Type[Warning], str, Optional[int], Optional[str])->str
    # simplify warning-message format
    return ('%s: %s\n' % (category.__name__, message))


warnings.formatwarning = formatwarning


class ParseError(Exception):
    pass


class InvalidInfoBlockError(ParseError):
    def __init__(self, actual):
        # type: (KeyType)->None
        self.actual = actual  # type: KeyType

    def __str__(self):
        # type: ()->str
        return 'INFO block must have (only) one KEY: {}'.format(self.actual)


class ParseWarning(UserWarning):
    def call(self):
        # type: ()->None
        warnings.warn(self)


class UnrecognizedLineWarning(ParseWarning):
    def __init__(self, line):
        # type: (str)->None
        self.line = line

    def __str__(self):
        # type: ()->str
        return 'Ignored "{}"'.format(self.line)


class OrphanLineWarning(ParseWarning):
    def __init__(self, line):
        # type: (str)->None
        self.line = line

    def __str__(self):
        # type: ()->str
        return 'Ignored "{}"'.format(self.line)


class InvalidFormatWarning(ParseWarning):
    def __init__(self, line, block_title=''):
        # type: (str, str)->None
        self.line = line
        self.block_title = block_title

    def __str__(self):
        # type: ()->str
        block_info = 'in ' + self.block_title if self.block_title else ''
        return 'Ignored {}"{}"'.format(block_info, self.line)


class DumpWarning(UserWarning):
    def call(self):
        # type: ()->None
        warnings.warn(self)


class OrphanCommentWarning(DumpWarning):
    def __init__(self, line):
        # type: (List[yaslha.line.CommentLine])->None
        self.line = line

    def __str__(self):
        # type: ()->str
        return 'Removed orphan comment "{}"'.format(self.line)


class UnrecognizedLineObjectWarning(DumpWarning):
    def __init__(self, obj):
        # type: (yaslha.line.AbsLine)->None
        self.obj = obj

    def __str__(self):
        # type: ()->str
        return 'Ignored an unknown line "{}"'.format(self.obj)
