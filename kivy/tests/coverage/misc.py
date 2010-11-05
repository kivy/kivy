"""Miscellaneous stuff for Coverage."""

def nice_pair(pair):
    """Make a nice string representation of a pair of numbers.

    If the numbers are equal, just return the number, otherwise return the pair
    with a dash between them, indicating the range.

    """
    start, end = pair
    if start == end:
        return "%d" % start
    else:
        return "%d-%d" % (start, end)


def format_lines(statements, lines):
    """Nicely format a list of line numbers.

    Format a list of line numbers for printing by coalescing groups of lines as
    long as the lines represent consecutive statements.  This will coalesce
    even if there are gaps between statements.

    For example, if `statements` is [1,2,3,4,5,10,11,12,13,14] and
    `lines` is [1,2,5,10,11,13,14] then the result will be "1-2, 5-11, 13-14".

    """
    pairs = []
    i = 0
    j = 0
    start = None
    while i < len(statements) and j < len(lines):
        if statements[i] == lines[j]:
            if start == None:
                start = lines[j]
            end = lines[j]
            j += 1
        elif start:
            pairs.append((start, end))
            start = None
        i += 1
    if start:
        pairs.append((start, end))
    ret = ', '.join(map(nice_pair, pairs))
    return ret


def expensive(fn):
    """A decorator to cache the result of an expensive operation.

    Only applies to methods with no arguments.

    """
    attr = "_cache_" + fn.__name__
    def _wrapped(self):
        """Inner fn that checks the cache."""
        if not hasattr(self, attr):
            setattr(self, attr, fn(self))
        return getattr(self, attr)
    return _wrapped


def bool_or_none(b):
    """Return bool(b), but preserve None."""
    if b is None:
        return None
    else:
        return bool(b)


class CoverageException(Exception):
    """An exception specific to Coverage."""
    pass

class NoSource(CoverageException):
    """Used to indicate we couldn't find the source for a module."""
    pass

class ExceptionDuringRun(CoverageException):
    """An exception happened while running customer code.

    Construct it with three arguments, the values from `sys.exc_info`.

    """
    pass
