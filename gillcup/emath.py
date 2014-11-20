import builtins
import math

from gillcup import expressions


class _UnaryMap(expressions.Map):
    def __init__(self, exp):
        super().__init__(type(self).func, exp)


def _make_unary_map(name, func, doc):
    members = {'func': func, '__doc__': doc, 'prettyname': name}
    return type(name, (_UnaryMap, ), members)


def _unary_map(func):
    return _make_unary_map(func.__name__, func, func.__doc__)


class _SeqMap(expressions.Map):
    def __init__(self, *expressions):
        super().__init__(type(self).func, *expressions)


def _seq_map(func):
    members = {'func': func, '__doc__': func.__doc__}
    return type(func.__name__, (_SeqMap, ), members)


class round(expressions.Map):
    """Element-wise round to even

    >>> round((1.25, 2.5, 3.5))
    <1.0, 2.0, 4.0>
    >>> round((1.25, 2.5, 3.5), ndigits=1)
    <1.2, 2.5, 3.5>
    """
    prettyname = 'round'

    def __init__(self, expression, ndigits=0):
        self.ndigits = ndigits
        super().__init__(self.func, expression)

    def func(self, x):
        return float(builtins.round(x, ndigits=self.ndigits))


class log(expressions.Map):
    """Element-wise logarithm

    >>> log((0, 1, 10), 10)
    <nan, 0.0, 1.0>
    >>> round(log((0, 1, 10)), 4)
    <nan, 0.0, 2.3026>
    """
    prettyname = 'log'

    def __init__(self, expression, base='e'):
        if base == 'e':
            self._logfunc = math.log
        elif base == 2:
            self._logfunc = math.log2
        elif base == 10:
            self._logfunc = math.log10
        else:
            self._logfunc = functools.partial(math.log, base=base)
        super().__init__(self.func, expression)

    def func(self, x):
        try:
            return self._logfunc(x)
        except ValueError:
            return float('nan')


abs = _make_unary_map('abs', math.fabs, """Element-wise absolute value""")

@_unary_map
def ceil(x):
    """Element-wise round up

    >>> ceil((1.25, -2.5, 3.5))
    <2.0, -2.0, 4.0>
    """
    return float(math.ceil(x))


@_unary_map
def floor(x):
    """Element-wise round down

    >>> floor((1.25, -2.5, 3.5))
    <1.0, -3.0, 3.0>
    """
    return float(math.floor(x))


@_unary_map
def trunc(x):
    """Element-wise truncation to integer

    >>> trunc((1.25, -2.5, 3.5))
    <1.0, -2.0, 3.0>
    """
    return float(math.trunc(x))



def map(func, *arguments):
    """Applies a function element-wise on Expressions.

    Unlike the Python built-in :func:`map`, this assumes that ``func`` is
    a *pure* function: no side effects, value depends on the arguments only.

    >>> map(lambda a, b: a + b, (1, 2, 3), (1, 2, 3))
    <2.0, 4.0, 6.0>
    """
    return expressions.Map(func, *arguments)


@_seq_map
def max(*values):
    """Element-wise maximum

    >>> max((1, 2, 3), (3, 2, 1))
    <3.0, 2.0, 3.0>
    """
    return builtins.max(values)


@_seq_map
def min(*values):
    """Element-wise minimum

    >>> min((1, 2, 3), (3, 2, 1))
    <1.0, 2.0, 1.0>
    """
    return builtins.min(values)


isfinite = _make_unary_map('isfinite', math.isfinite, """Element-wise test for infinity or NaN""")
isinf = _make_unary_map('isinf', math.isinf, """Element-wise test for infinity (positive or negative)""")
isnan = _make_unary_map('isnan', math.isnan, """Element-wise test for NaN""")

acos = _make_unary_map('acos', math.acos, """Element-wise arc cosine""")
acosh = _make_unary_map('acosh', math.acosh, """Element-wise hyperbolic arc cosine""")
asin = _make_unary_map('asin', math.asin, """Element-wise arc sine""")
atan = _make_unary_map('atan', math.atan, """Element-wise arc tangent""")
atan2 = _make_unary_map('atan2', math.atan2, """Element-wise sign-considering arc tangent""")
atanh = _make_unary_map('atanh', math.atanh, """Element-wise hyperbolic arc tangent""")
cos = _make_unary_map('cos', math.cos, """Element-wise cosine""")
cosh = _make_unary_map('cosh', math.cosh, """Element-wise hyperbolic cosine""")
sin = _make_unary_map('sin', math.sin, """Element-wise sine""")
sinh = _make_unary_map('sinh', math.sinh, """Element-wise hyperbolic sine""")
tan = _make_unary_map('tan', math.tan, """Element-wise tangent""")
tanh = _make_unary_map('tanh', math.tanh, """Element-wise hyperbolic tangent""")
degrees = _make_unary_map('degrees', math.degrees, """Element-wise radians-to-degrees conversion""")
radians = _make_unary_map('radians', math.radians, """Element-wise degrees-to-radians conversion""")

@_unary_map
def sqrt(x):
    """Element-wise square root"""
    try:
        return math.sqrt(x)
    except ValueError:
        return float('nan')

exp = _make_unary_map('exp', math.exp, """Element-wise ``e**x``""")
expm1 = _make_unary_map('expm1', math.expm1, """Element-wise ``e**x - 1``""")
hypot = _make_unary_map('hypot', math.hypot, """Element-wise Euclidean norm""")
erf = _make_unary_map('errf', math.erf, """Element-wise Gaus error function""")


@_unary_map
def sign(x):
    """Element-wise signum

    >>> sign((-10, 0, 2))
    <-1.0, 0.0, 1.0>
    """
    if x > 0:
        return 1.0
    elif x < 0:
        return -1.0
    else:
        return 0.0
