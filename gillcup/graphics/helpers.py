
import operator
import functools
from contextlib import contextmanager

def extend_tuple(args, default=0):
    """Extend the given tuple to a triple, padding by the given value
    """
    try:
        x, y, z = args
    except StandardError:
        try:
            x, y = args
            z = default
        except StandardError:
            try:
                x, = args
            except StandardError:
                x = args
            y = z = default
    return x, y, z

def extend_tuple_copy(args):
    """Extend the given tuple to a triple, copying the last value
    """
    try:
        x, y, z = args
    except StandardError:
        try:
            x, y = args
            z = y
        except StandardError:
            try:
                x, = args
            except StandardError:
                x = args
            y = z = x
    return x, y, z

@contextmanager
def nullContextManager(*args, **kwargs):
    """A context manager that does nothing
    """
    yield

def tuple_multiply(*tuples):
    return tuple(functools.reduce(operator.mul, items) for items in zip(*tuples))
