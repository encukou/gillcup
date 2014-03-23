import operator
import functools
import math


@functools.total_ordering
class Expression:
    """A dynamic numeric value.

    This is a base class, do not use it directly.
    """

    def __len__(self):
        return len(self.get())

    def __iter__(self):
        return iter(self.get())

    def __float__(self):
        value = self.get()
        try:
            [number] = value
        except ValueError:
            raise ValueError('need one component, not {}'.format(len(self)))
        return float(number)

    def __int__(self):
        return int(float(self))

    def __repr__(self):
        return '<{}>'.format(', '.join(str(n) for n in self))

    def get(self):
        """Return the value of this expression, as a tuple"""
        raise NotImplementedError()

    def simplify(self):
        return self

    @property
    def children(self):
        return ()

    @property
    def pretty_name(self):
        return type(self).__name__

    def __eq__(self, other):
        return self.get() == _as_tuple(other)

    def __lt__(self, other):
        return self.get() < _as_tuple(other)

    def __add__(self, other):
        return Sum((self, other)).simplify()
    __radd__ = __add__

    def __mul__(self, other):
        return Product((self, other)).simplify()
    __rmul__ = __mul__

    def __sub__(self, other):
        return Difference((self, other)).simplify()

    def __rsub__(self, other):
        return Difference((other, self)).simplify()

    def __truediv__(self, other):
        return Quotient((self, other)).simplify()

    def __rtruediv__(self, other):
        return Quotient((other, self)).simplify()

    def __pos__(self):
        return self

    def __neg__(self):
        return Neg(self).simplify()


def dump(exp, indent=0):
    base = '{dent}{name} {exp!r}'.format(
        dent='  ' * indent,
        name=exp.pretty_name,
        exp=exp)
    children = list(exp.children)
    if children:
        return base + ':\n' + '\n'.join(dump(c, indent+1) for c in children)
    else:
        return base


def _as_tuple(value, size=1):
    if isinstance(value, Expression):
        return value.get()
    try:
        iterator = iter(value)
    except TypeError:
        return (float(value), ) * size
    else:
        return tuple(float(v) for v in iterator)


class Constant(Expression):
    def __init__(self, *value):
        self._value = tuple(float(v) for v in value)

    def get(self):
        return self._value


class Value(Expression):
    def __init__(self, *value):
        self._value = tuple(float(v) for v in value)
        self._size = len(self._value)

    def __len__(self):
        return self._size

    def get(self):
        return self._value

    def set(self, *value):
        value = tuple(float(v) for v in value)
        if len(value) != self._size:
            raise ValueError('Mismatched vector size: {} != {}'.format(
                len(value), self._size))
        self._value = value


def _coerce(exp, size=1):
    if isinstance(exp, Expression):
        return exp
    else:
        return Constant(*_as_tuple(exp, size))


def _coerce_all(exps):
    exps = tuple(exps)
    for exp in exps:
        try:
            size = len(exp)
        except TypeError:
            pass
        else:
            break
    else:
        raise ValueError('Unable to determine size: %s' % exps)
    return tuple(_coerce(e, size) for e in exps)


def _fold_tuples(operands, op):
    reducer = functools.partial(functools.reduce, op)
    return tuple(map(reducer, zip(*operands)))


def _check_len(a, b):
    if len(a) != len(b):
        raise ValueError('Mismatched vector size: {} != {}'.format(
            len(a), len(b)))


class Foldr(Expression):
    def __init__(self, operands, op):
        self._op = op
        self._operands = tuple(_coerce_all(operands))
        first = self._operands[0]
        for operand in self._operands[1:]:
            _check_len(operand, first)

    def get(self):
        return _fold_tuples(self._operands, self._op)

    @property
    def pretty_name(self):
        return '{}({})'.format(type(self).__name__, self._op)

    @property
    def children(self):
        return self._operands

    def simplify(self):
        if all(isinstance(o, Constant) for o in self._operands):
            return Constant(*self.get())
        else:
            return self


class Sum(Foldr):
    pretty_name = '+'

    def __init__(self, operands):
        super().__init__(operands, operator.add)

    def _dump_name(self):
        return '+'


class Product(Foldr):
    pretty_name = '*'

    def __init__(self, operands):
        super().__init__(operands, operator.mul)


class Difference(Foldr):
    pretty_name = '-'

    def __init__(self, operands):
        super().__init__(operands, operator.sub)


def safediv(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        sign = a * b
        if a and not math.isnan(a):
            return math.copysign(float('inf'), sign)
        else:
            return float('nan')

class Quotient(Foldr):
    pretty_name = '/'

    def __init__(self, operands):
        super().__init__(operands, safediv)


class Elementwise(Expression):
    def __init__(self, operand, op):
        self._operand = _coerce(operand)
        self._op = op

    def get(self):
        return tuple(map(self._op, self._operand.get()))

    @property
    def children(self):
        yield self._operand


class Neg(Elementwise):
    def __init__(self, operand):
        super().__init__(operand, operator.neg)

    def simplify(self):
        if isinstance(self._operand, Constant):
            return Constant(*self.get())
        else:
            return self
