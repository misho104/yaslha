import warnings


def formatwarning(message, category, filename, lineno, line=None):
    # simplify warning-message format
    return ('%s: %s\n' % (category.__name__, message))


warnings.formatwarning = formatwarning


class ParseError(Exception):
    pass


class InvalidInfoBlockError(ParseError):
    def __init__(self, actual):
        self.actual = actual

    def __str__(self):
        return f'INFO block must have (only) one KEY: {self.actual}'


class ParseWarning(UserWarning):
    def call(self):
        warnings.warn(self)


class UnrecognizedLineWarning(ParseWarning):
    def __init__(self, line):
        self.line = line

    def __str__(self):
        return f'Ignored "{self.line}"'


class OrphanLineWarning(ParseWarning):
    def __init__(self, line):
        self.line = line

    def __str__(self):
        return f'Ignored "{self.line}"'


class InvalidFormatWarning(ParseWarning):
    def __init__(self, line, block_title=None):
        self.line = line
        self.block_title = block_title

    def __str__(self):
        block_info = f'in {self.block_title} ' if self.block_title else ''
        return f'Ignored {block_info}"{self.line}"'


class DumpWarning(UserWarning):
    def call(self):
        warnings.warn(self)


class OrphanCommentWarning(DumpWarning):
    def __init__(self, line):
        self.line = line

    def __str__(self):
        return f'Removed orphan comment "{self.line}""'


class UnrecognizedLineObjectWarning(DumpWarning):
    def __init__(self, obj):
        self.obj = obj

    def __str__(self):
        return f'Ignored an unknown line "{self.obj}""'
