
from contextlib import contextmanager

def extend_tuple(args, default=0):
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
    yield
