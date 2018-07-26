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
        return 'INFO block must have (only) one KEY: ' + self.actual


class ParseWarning(UserWarning):
    def call(self):
        warnings.warn(self)


class UnrecognizedLineWarning(ParseWarning):
    def __init__(self, line):
        self.line = line

    def __str__(self):
        return 'Ignored "{}"'.format(self.line)


class OrphanLineWarning(ParseWarning):
    def __init__(self, line):
        self.line = line

    def __str__(self):
        return 'Ignored "{}"'.format(self.line)


class InvalidFormatWarning(ParseWarning):
    def __init__(self, line, block_title=None):
        self.line = line
        self.block_title = block_title

    def __str__(self):
        block_info = 'in ' + self.block.title if self.block_title else ''
        return 'Ignored {}"{}"'.format(block_info, self.line)


class DumpWarning(UserWarning):
    def call(self):
        warnings.warn(self)


class OrphanCommentWarning(DumpWarning):
    def __init__(self, line):
        self.line = line

    def __str__(self):
        return 'Removed orphan comment "{}"'.format(self.line)


class UnrecognizedLineObjectWarning(DumpWarning):
    def __init__(self, obj):
        self.obj = obj

    def __str__(self):
        return 'Ignored an unknown line "{}"'.format(self.obj)
