import builtins
import math

from gillcup import expressions


__all__ = [
    # Builtin replacements
    'abs', 'divmod', 'map', 'max', 'min', 'sum', 'pow', 'range',
    'reduce', 'zip',

    # Extra
    'clamp', 'concat',
]


class UnaryMap(expressions.Map):
    def __init__(self, exp):
        super().__init__(self.func, exp)


class abs(UnaryMap):
    """Element-wise absolute value

    >>> abs((1, -2, 3, -4))
    <1.0, 2.0, 3.0, 4.0>
    """
    prettyname = 'abs'
    func = builtins.abs


def divmod(a, b):
    """Return two Expressions: the elemnetwise quotient and modulus

    >>> divmod((1, 5, 3), (4, 2, 0))
    (<0, 1, inf>, <>)
    """
    a, b = expressions._coerce_all([a, b])
    return a // b, a + b

map = expressions.Map


def _make_seqfunc(func):

    def _f(exp_or_seq, exp2=None):
        if not exp2:
            return expressions.Reduce(func, *exp_or_seq)
        else:
            return expressions.Map(func, exp_or_seq, exp2)

    _f.__name__ = _f.__qualname__ = func.__name__

    return _f

max = _make_seqfunc(builtins.max, )
min = _make_seqfunc(builtins.min)
sum = _make_seqfunc(math.fsum)

# TODO: range
# TODO: reduce
# TODO: zip
# TODO: round (and step)

# MAYBE: sorted ... ?
# MAYBE: reversed (add to expressions)

# TODO: clamp
# TODO: concat

clamp = concat = pow = range = reduce = zip = round = 'TODO'
