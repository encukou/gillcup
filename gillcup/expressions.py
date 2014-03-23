import operator
import functools
import math


class EmptyExpressionError(ValueError):
    """Raised when a zero-length expression would be created"""
    def __init__(self, message='cannot create zero-length expression'):
        super().__init__(message)


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

    def __getitem__(self, index):
        return Slice(self, index)

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

    def replace(self, index, replacement):
        """Replace the given element (or slice) with a value

        Any element of an expression can be replaced::

            >>> Constant(1, 2, 3).replace(0, -2)
            <-2.0, 2.0, 3.0>

        This can be used to change the size of the expression
        (as long as it doesn't become zero)::

            >>> Constant(1, 2, 3).replace(0, (-2, -3))
            <-2.0, -3.0, 2.0, 3.0>

        Slices can be replaced as well::

            >>> Constant(1, 2, 3).replace(slice(0, -1), (-2, -3))
            <-2.0, -3.0, 3.0>

            >>> Constant(1, 2, 3).replace(slice(1, 1), (-8, -9))
            <1.0, -8.0, -9.0, 2.0, 3.0>

            >>> Constant(1, 2, 3).replace(slice(1, None), ())
            <1.0>

        When replacing a slice by a plain number, the number is repeated
        so that the size does not change::

            >>> Constant(1, 2, 3).replace(slice(0, -1), -1)
            <-1.0, -1.0, 3.0>
            >>> Constant(1, 2, 3).replace(slice(0, -1), (-1,))
            <-1.0, 3.0>

        Of course this does not happen when using a tuple or expression::

            >>> Constant(1, 2, 3).replace(slice(0, -1), Constant(-1))
            <-1.0, 3.0>
        """
        start, stop = _get_slice_indices(self, index, allow_empty=True)
        replacement = _coerce(replacement, stop - start, allow_empty=True)
        parts = []
        if start > 0:
            parts.append(self[:start])
        if replacement:
            parts.append(replacement)
        if stop < len(self):
            parts.append(self[stop:])
        if not parts:
            raise EmptyExpressionError()
        elif len(parts) == 1:
            return parts[0]
        else:
            return Concat(*parts).simplify()


def dump(exp):
    memo = {}
    seen = set()
    counter = 0

    def fill_memo(exp):
        nonlocal counter
        num = memo.get(id(exp), None)
        if num is None:
            memo[id(exp)] = 0
            for child in exp.children:
                fill_memo(child)
        elif not num:
            counter += 1
            memo[id(exp)] = counter

    fill_memo(exp)

    def gen(exp, indent=0):
        base = '{dent}{name} {exp!r}'.format(
            dent='  ' * indent,
            name=exp.pretty_name,
            exp=exp)
        children = list(exp.children)
        ref = memo[id(exp)]
        if id(exp) in seen:
            yield '{}  (*{})'.format(base, ref)
        else:
            seen.add(id(exp))
            if ref:
                refpart = '  (&{})'.format(ref)
            else:
                refpart = ''
            if children:
                yield base + ':' + refpart
                for child in exp.children:
                    yield from gen(child, indent + 1)
            else:
                yield base + refpart

    return '\n'.join(gen(exp))


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
        if not value:
            raise EmptyExpressionError()
        self._value = tuple(float(v) for v in value)

    def get(self):
        return self._value


class Value(Expression):
    def __init__(self, *value):
        if not value:
            raise EmptyExpressionError()
        self._value = tuple(float(v) for v in value)
        self._size = len(self._value)
        self._fixed = False

    def __len__(self):
        return self._size

    def get(self):
        return self._value

    def set(self, *value):
        if self._fixed:
            raise ValueError('value has been fixed')
        value = tuple(float(v) for v in value)
        if len(value) != self._size:
            raise ValueError('Mismatched vector size: {} != {}'.format(
                len(value), self._size))
        self._value = value

    def fix(self, *value):
        if value:
            self.set(*value)
        self._fixed = True

    @property
    def pretty_name(self):
        if self._fixed:
            return '{} (fixed)'.format(type(self).__name__)
        else:
            return type(self).__name__

    def simplify(self):
        if self._fixed:
            return Constant(*self)
        else:
            return self


def _coerce(exp, size=1, allow_empty=False):
    if isinstance(exp, Expression):
        return exp
    else:
        tup = _as_tuple(exp, size)
        if not tup:
            if allow_empty:
                return None
            else:
                raise EmptyExpressionError()
        else:
            return Constant(*tup)


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
        self._operands = tuple(o.simplify() for o in self._operands)
        if all(isinstance(o, Constant) for o in self._operands):
            return Constant(*self)
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
        if isinstance(self._operand.simplify(), Constant):
            return Constant(*self)
        else:
            return self


def _get_slice_indices(source, index, allow_empty=False):
        try:
            index = int(index)
        except TypeError:
            try:
                indices = index.indices
            except AttributeError:
                message = 'indices must be slices or integers, not {}'
                raise TypeError(message.format(type(index).__name__))
            start, stop, step = indices(len(source))
            if step not in (None, 1):
                raise IndexError('non-1 step not supported')
            if start >= stop and not allow_empty:
                raise EmptyExpressionError()
            return start, stop
        else:
            if index < 0:
                index += len(source)
            if not (0 <= index < len(source)):
                raise IndexError('expression index out of range')
            return index, index + 1


class Slice(Expression):
    def __init__(self, source, index):
        self._source = source
        self._start, self._stop = _get_slice_indices(source, index)
        self._len = self._stop - self._start

    def __len__(self):
        return self._len

    @property
    def pretty_name(self):
        return '[{}:{}]'.format(self._start, self._stop)

    @property
    def children(self):
        yield self._source

    def get(self):
        return self._source.get()[self._start:self._stop]


class Concat(Expression):
    def __init__(self, *children):
        self._children = tuple(_coerce(c) for c in children)
        if not self._children:
            raise ValueError('no expressions to concatentate')
        self._len = sum(len(c) for c in self._children)
        self._simplify_children()

    @property
    def children(self):
        return self._children

    def __len__(self):
        return self._len

    def get(self):
        return sum((c.get() for c in self._children), ())

    def simplify(self):
        self._simplify_children()
        if len(self._children) == 1:
            return self._children[0]
        else:
            return self

    def _simplify_children(self):
        new_children = []
        for child in self._children:
            child = child.simplify()
            if (isinstance(child, Constant) and
                    new_children and
                    isinstance(new_children[-1], Constant)):
                new_const = Constant(*new_children[-1].get() + child.get())
                new_children[-1] = new_const
            else:
                new_children.append(child)
        self._children = tuple(new_children)
