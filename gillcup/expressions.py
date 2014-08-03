"""Dynamic numeric value primitives

This module makes it possible to define arithmetic expressions that are
evaluated at run-time.
For example, given an Expression ``x``, the Expression ``x * 2`` will
always evaulate to twice the value of ``x``.

The power of Expressions becomes apparent when we mention that
:class:`~gillcup.clock.Clock` time can be used an input.
Gillcup includes expression that smoothly changes value as time progresses.
Combined with other expressions, "animations" on numbers can be created.

Gillcup's expressions can simplify themselves,
so that e.g. a sum of constants (``1 + 2``) becomes a single constant (``3``).
When an animation ends, the fact that Gillcup time cannot go backwards usually
makes it possible to remove the dynamic aspect of the expression involved.

Gillcup expressions are actually 1-D vectors.
Each Expression has a fixed :term:`size` that determines how many
numbers it contains.
Operations such as addition are element-wise (``<1, 2> + <3, 4> == <4, 6>``).
To get the value of an Expression, use either the :meth:`~Expression.get`
method, or iterate the Expression::

    >>> exp = Constant(1, 2, 3)
    >>> exp
    <1.0, 2.0, 3.0>

    >>> tuple(exp)
    (1.0, 2.0, 3.0)

    >>> x, y, z = exp
    >>> print(x, y, z)
    1.0 2.0 3.0

Expressions with a single component can be converted directly to a number::

    >>> exp = Constant(1.5)
    >>> exp
    <1.5>

    >>> float(exp)
    1.5

    >>> int(exp)
    1

Expression values are floating-point numbers,
so they cannot be used for precise computation [#goldberg]_.
Gillcup expressions are geared for smooth interpolation,
not for high mathematics on custom types.

.. (the real reason for just using floats is possibility of
   C-level optimizations)

Most Expressions are immutable, but their *values* can change ofer time.
For example, there is no way to change ``x + 1`` to ``x - 3``, but the value
of ``x`` is potentially recomputed on every access.

Compound Expressions, and operators such as ``+``, ``-``, or ``/`` that
create them, take other expressions as arguments.
Instead of expressions, they accept tuples of the appropriate size,
or plain numbers.
If a plain number is given where a multi-element expression is required,
the number will be repeated::

    >>> Value(1, 2, 3) + (10, 10, 10)
    <11.0, 12.0, 13.0>
    >>> Value(1, 2, 3) + 10
    <11.0, 12.0, 13.0>
    >>> Sum([Value(1, 2, 3), 10])
    <11.0, 12.0, 13.0>

.. rubric:: Footnotes

.. [#goldberg] The obligatory link to David Goldberg's paper
    *What Every Computer Scientist Should Know About Floating-Point Arithmetic*
    is
    `here <http://docs.oracle.com/cd/E19957-01/806-3568/ncg_goldberg.html>`_.


Reference
---------

.. autoclass:: gillcup.expressions.Expression

Basic Expressions
-----------------

.. autoclass:: gillcup.expressions.Constant
.. autoclass:: gillcup.expressions.Value
.. autoclass:: gillcup.expressions.Progress

Compound Expressions
--------------------

.. autoclass:: gillcup.expressions.Reduce
.. autoclass:: gillcup.expressions.Elementwise
.. autoclass:: gillcup.expressions.Interpolation

Arithmetic Expressions
......................

For the following, using the appropriate operator is preferred
to constructing them directly:

.. autoclass:: gillcup.expressions.Sum
.. autoclass:: gillcup.expressions.Product
.. autoclass:: gillcup.expressions.Difference
.. autoclass:: gillcup.expressions.Quotient
.. autoclass:: gillcup.expressions.Neg

.. autoclass:: gillcup.expressions.Slice
.. autoclass:: gillcup.expressions.Concat

Debugging helpers
-----------------

.. autofunction:: gillcup.expressions.dump
.. autoclass:: gillcup.expressions.NamedContainer


Helpers
-------

.. autofunction:: gillcup.expressions.simplify
.. autofunction:: gillcup.expressions.safediv

"""

import operator
import functools
import math

from gillcup.signals import signal


def simplify(exp):
    """Return a simplified version the given expression, if it exists"""
    return exp.replacement


@functools.total_ordering
class Expression:
    """A dynamic numeric value.

    This is a base class, subclass it but do not use it directly.

    Subclassing reference:

        Overridable members:

            .. automethod:: get
            .. autoattribute:: children
            .. autoattribute:: pretty_name

        Replacing:

            Sometimes when an expression is simplified, it may make sense to
            replace it by a different type.
            For example, after an animation ends the value will not change
            any more, and can be represented by a Constant.

            To make a request for such a replacement, store the new expression
            in the :attr:`replacement` attribute.
            This will automatically trigger the :meth:`replacement_available`
            signal.

            .. autoattribute:: replacement
            .. automethod:: replacement_available

    Operations:
        .. autospecialmethod:: __len__
        .. autospecialmethod:: __iter__
        .. autospecialmethod:: __float__
        .. autospecialmethod:: __int__
        .. autospecialmethod:: __getitem__
        .. automethod:: replace
        .. function:: self == other
                      self != other
                      self < other
                      self <= other
                      self > other
                      self >= other

                *a.k.a.* :token:`__eq__(other)` etc.

                Compare the *value* of this expression,
                element-wise (as a tuple), to :token:`other`.

                :token:`other` may be be an expression or a tuple.

                :token:`other` may also be a real number,
                which is only equal to one-element expressions

        .. function:: self + other
                      self - other
                      self * other
                      self / other

                *a.k.a.* :token:`__add__(other)` etc.

                Return a nes Expression that evluates an element-wise operation
                on the value.

                These operations create a :class:`Sum`, :class:`Difference`,
                :class:`Product`, or :class:`Quotient`, respectively.

                The reverse operations (``other + self``/``__radd__``, etc)
                are also supported.

        .. autospecialmethod:: __pos__
        .. autospecialmethod:: __neg__
    """

    @signal
    def replacement_available():
        """Notifies that a simplified replacement is available"""

    def __len__(self):
        """Size of this expression

        This must be constant throughout the life of the expression.

        The base class wastefully calls :meth:`get`; override if possible.
        """
        return len(self.get())

    def __iter__(self):
        """Iterator over this expression's current value"""
        return iter(self.get())

    def __float__(self):
        """For one-element Expressions, return the numeric value.

        Raises :class:`ValueError` for other Expressions.
        """
        value = self.get()
        try:
            [number] = value
        except ValueError:
            raise ValueError('need one component, not {}'.format(len(self)))
        return float(number)

    def __int__(self):
        """Returns ``int(float(exp))``."""
        return int(float(self))

    def __repr__(self):
        return '<{}>'.format(', '.join(str(n) for n in self))

    def get(self):
        """Return the current value of this expression, as a tuple."""
        raise NotImplementedError()

    @property
    def replacement(self):
        """A simplified version of this expression

        If a simplified version does not exist, the value is self.
        """
        replacement = self._replacement
        if replacement is None:
            return self
        else:
            while replacement._replacement is not None:
                replacement = replacement._replacement
            self._replacement = replacement
            return replacement

    @replacement.setter
    def replacement(self, new_exp):
        if new_exp is not self._replacement:
            self._replacement = new_exp
            self.replacement_available()
    _replacement = None

    @property
    def children(self):
        """The children of this Expression

        This attribute gives an iterable over the components, or inputs,
        of this Expression.
        It is used in pretty-printing and dumping the structure of expressions.

        See :func:`dump` for more discussion.
        """
        return ()

    @property
    def pretty_name(self):
        """Name for pretty-printing
        """
        return type(self).__name__

    def __getitem__(self, index):
        """Take a slice this expression using standard Python slicing rules

        >>> exp = Constant(1, 2, 3)
        >>> exp[0]
        <1.0>
        >>> exp[:-1]
        <1.0, 2.0>
        """
        return simplify(Slice(self, index))

    def __eq__(self, other):
        return self.get() == _as_tuple(other)

    def __lt__(self, other):
        return self.get() < _as_tuple(other)

    def __add__(self, other):
        return simplify(Sum((self, other)))
    __radd__ = __add__

    def __mul__(self, other):
        return simplify(Product((self, other)))
    __rmul__ = __mul__

    def __sub__(self, other):
        return simplify(Difference((self, other)))

    def __rsub__(self, other):
        return simplify(Difference((other, self)))

    def __truediv__(self, other):
        return simplify(Quotient((self, other)))

    def __rtruediv__(self, other):
        return simplify(Quotient((other, self)))

    def __pos__(self):
        """Return this Expression unchanged"""
        return self

    def __neg__(self):
        """Return an element-wise negation of this Expression"""
        return Neg(self).simplify()

    def replace(self, index, replacement):
        """Replace the given element (or slice) with a value

        (This is the equivalent of :token:`__setitem__`, but it returns a new
        Expression instead of modifying the old.)

        :param index: Index, or slice, to be replaced
        :param replacement: The new value
        :type replacement: Expression, tuple, or a simple number

        Any element of an expression can be replaced::

            >>> Constant(1, 2, 3).replace(0, -2)
            <-2.0, 2.0, 3.0>

        This can be used to change the size of the expression::

            >>> Constant(1, 2, 3).replace(0, (-2, -3))
            <-2.0, -3.0, 2.0, 3.0>

        Slices can be replaced as well::

            >>> Constant(1, 2, 3).replace(slice(0, -1), (-2, -3))
            <-2.0, -3.0, 3.0>

            >>> Constant(1, 2, 3).replace(slice(1, 1), (-8, -9))
            <1.0, -8.0, -9.0, 2.0, 3.0>

            >>> Constant(1, 2, 3).replace(slice(1, None), ())
            <1.0>

            >>> Constant(1, 2, 3).replace(slice(None, None), ())
            <>

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
        start, stop = _get_slice_indices(self, index)
        replacement = _coerce(replacement, stop - start)
        return simplify(Concat(self[:start], replacement, self[stop:]))


def dump(exp):
    """Return a pretty-printed tree of an Expression and its children

    Formats the value, :attr:`~Expression.pretty_name`, and, recursively,
    :attr:`~Expression.children`, of the given Expression
    arranged in a tree-like structure.

        >>> exp = Value(0) + Value(1) / Value(2)
        >>> print(dump(exp))
        + <0.5>:
          Value <0.0>
          / <0.5>:
            Value <1.0>
            Value <2.0>

    Expressions are encouraged to "lie" about their structure in
    :attr:`~Expression.children`, if it leads to better readibility.
    For example, an expression with several heterogeneous children
    can wrap each child in a :class:`NamedContainer`::

        >>> exp = Interpolation(Value(0), Value(10), Value(0.5))
        >>> print(dump(exp))
        Interpolation <5.0>:
          from <0.0>:
            Value <0.0>
          to <10.0>:
            Value <10.0>
          t <0.5>:
            Value <0.5>

    Here the ``from``, ``to``, and ``t`` are dynamically generated
    :class:`NamedContainers <NamedContainer>` whose only purpose is to make
    the dump more readable.
    """

    # Maps id() of every seen expression to the reference used for it
    memo = {}

    # holds the id() of all seen expressions
    seen = set()

    # holds all seen expressions (so they don't get garbage-collected and
    # replaced by a different expr with the same id)
    seen_list = []

    # Current reference value
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
        ref = memo.get(id(exp), None)
        if id(exp) in seen:
            yield '{}  (*{})'.format(base, ref)
        else:
            seen.add(id(exp))
            seen_list.append(exp)
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


def _replace_child(exp, listener):
    """Move listener from an expression to its replacement, return replacement
    """
    replacement = exp.replacement
    if replacement is exp:
        return exp
    else:
        exp.replacement_available.disconnect(listener)
        if not isinstance(replacement, Constant):
            replacement.replacement_available.connect(listener)
        return replacement


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
    """A constant expression.

    The value of this expression cannot be changed.
    """
    def __init__(self, *value):
        self._value = tuple(float(v) for v in value)

    def get(self):
        return self._value

    def __getitem__(self, index):
        return Constant(*self._value[slice(*_get_slice_indices(self, index))])


class Value(Expression):
    """A mutable value.

    Methods:
        .. automethod:: set
        .. automethod:: fix
    """
    def __init__(self, *value):
        self._value = tuple(float(v) for v in value)
        self._size = len(self._value)
        self._fixed = False

    def __len__(self):
        return self._size

    def get(self):
        return self._value

    def set(self, *value):
        """Set the value

            >>> exp = Value(1, 2, 3)
            >>> exp
            <1.0, 2.0, 3.0>
            >>> exp.set(3, 2, 1)
            >>> exp
            <3.0, 2.0, 1.0>

        The :attr:`size` of the new value must be equal to the old one.

        The value cannot be changed after :meth:`fix` is called.
        """
        if self._replacement is not None:
            raise ValueError('value has been fixed')
        value = tuple(float(v) for v in value)
        if len(value) != self._size:
            raise ValueError('Mismatched vector size: {} != {}'.format(
                len(value), self._size))
        self._value = value

    def fix(self, *value):
        """Freezes the current value.

        After a call to :token:`fix()`, the value becomes immutable,
        and the expression can be simplified to a :class:`Constant`.

        If arguments are given, they are passed to :meth:`set` before freezing.
        """
        if value:
            self.set(*value)
        self.replacement = Constant(*self)

    @property
    def pretty_name(self):
        if self._fixed:
            return '{} (fixed)'.format(type(self).__name__)
        else:
            return type(self).__name__


def _coerce(exp, size=1):
    if isinstance(exp, Expression):
        return simplify(exp)
    else:
        tup = _as_tuple(exp, size)
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
        size = 1
    return tuple(_coerce(e, size) for e in exps)


def _reduce_tuples(operands, op):
    reducer = functools.partial(functools.reduce, op)
    return tuple(map(reducer, zip(*operands)))


def _check_len(a, b):
    if len(a) != len(b):
        raise ValueError('Mismatched vector size: {} != {}'.format(
            len(a), len(b)))


class Reduce(Expression):
    """Applies an :func:`reduce` element-wise on a number of Expressions.

    All operands must be the same size.
    """
    def __init__(self, operands, op):
        self._op = op
        self._operands = tuple(_coerce_all(operands))
        first = self._operands[0]
        for operand in self._operands[1:]:
            _check_len(operand, first)
        for i, oper in enumerate(self._operands):
            oper.replacement_available.connect(self._replace_operands)
        self._replace_operands()

    def get(self):
        return _reduce_tuples(self._operands, self._op)

    @property
    def pretty_name(self):
        return '{}({})'.format(type(self).__name__, self._op)

    @property
    def children(self):
        return self._operands

    def _replace_operands(self):
        in_consts = True
        new = []
        for oper in self._operands:
            oper = _replace_child(oper.replacement, self._replace_operands)
            if in_consts and not isinstance(oper, Constant):
                if new:
                    new = [Constant(*_reduce_tuples(new, self._op))]
                in_consts = False
            new.append(oper)
        if in_consts:
            new = [Constant(*_reduce_tuples(new, self._op))]
        self._operands = new
        if len(self._operands) == 1:
            [self.replacement] = self._operands


class Sum(Reduce):
    """Element-wise sum of same-sized expressions

    All operands must be the same size.
    """
    pretty_name = '+'

    def __init__(self, operands):
        super().__init__(operands, operator.add)

    def _dump_name(self):
        return '+'


class Product(Reduce):
    """Element-wise product of same-sized expressions

    All operands must be the same size.
    """
    pretty_name = '*'

    def __init__(self, operands):
        super().__init__(operands, operator.mul)


class Difference(Reduce):
    """Element-wise difference of same-sized expressions

    All operands must be the same size.
    """
    pretty_name = '-'

    def __init__(self, operands):
        super().__init__(operands, operator.sub)


def safediv(a, b):
    """Divide a by b, but return NaN or infinity on division by zero

    The behavior is equivalent to Numpy with the 'ignore' setting.
    """
    try:
        return a / b
    except ZeroDivisionError:
        sign = a * b
        if a and not math.isnan(a):
            return math.copysign(float('inf'), sign)
        else:
            return float('nan')


class Quotient(Reduce):
    """Element-wise quotient of same-sized expressions

    All operands must be the same size.

    Division by zero will result in NaN or infinity, rather than raising
    an exception -- see :func:`safediv`.
    """
    pretty_name = '/'

    def __init__(self, operands):
        super().__init__(operands, safediv)


class Elementwise(Expression):
    """Applies a function element-wise on a single Expression.

    Assumes the `op` function is pure.
    """
    def __init__(self, operand, op):
        self._operand = _coerce(operand)
        self._op = op
        self._operand.replacement_available.connect(self._replace_operand)

    def get(self):
        return tuple(map(self._op, self._operand.get()))

    @property
    def children(self):
        yield self._operand

    def _replace_operand(self):
        self._operand = _replace_child(self._operand, self._replace_operand)
        if isinstance(self._operand, Constant):
            self.replacement = Constant(*self)


class Neg(Elementwise):
    """Element-wise negation"""
    def __init__(self, operand):
        super().__init__(operand, operator.neg)


def _get_slice_indices(source, index):
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
        return start, stop
    else:
        if index < 0:
            index += len(source)
        if not (0 <= index < len(source)):
            raise IndexError('expression index out of range')
        return index, index + 1


class Slice(Expression):
    """Slice of an Expression

    Typical result of an `exp[start:stop]` operation
    """
    def __init__(self, source, index):
        self._source = simplify(source)
        self._start, self._stop = _get_slice_indices(source, index)
        self._len = self._stop - self._start
        if self._len <= 0:
            self.replacement = Constant()
            self._len = 0
        elif self._start <= 0 and self._stop >= len(source):
            self.replacement = source
        elif isinstance(source, Slice):
            subslice = slice(self._start + src._start, self._stop + src._start)
            self.replacement = Slice(src._source, subslice)
        else:
            source.replacement_available.connect(self._replace_source)

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

    def _replace_source(self):
        self._source = src = _replace_child(self._source, self._replace_source)
        if isinstance(src, Constant):
            self.replacement = Constant(*self)


class Concat(Expression):
    """Concatenation of several Expressions.

    >>> Concat(Constant(1, 2), Constant(3))
    <1.0, 2.0, 3.0>

    Usually created as a result of :meth:`~Expression.replace`.
    """
    def __init__(self, *children):
        self._children = tuple(_coerce(c) for c in children)
        self._len = sum(len(c) for c in self._children)
        self._simplify_children()
        for child in children:
            child.replacement_available.connect(self._simplify_children)

    @property
    def children(self):
        return self._children

    def __len__(self):
        return self._len

    def get(self):
        return sum((c.get() for c in self._children), ())

    def _simplify_children(self):
        def gen_children(children):
            for child in children:
                if isinstance(child, Concat):
                    yield from gen_children(child._children)
                else:
                    yield child
        new_children = []
        for child in gen_children(self._children):
            child = simplify(child)
            if (isinstance(child, Constant) and
                    new_children and
                    isinstance(new_children[-1], Constant)):
                new_const = Constant(*new_children[-1].get() + child.get())
                new_children[-1] = new_const
            else:
                new_children.append(child)
        self._children = tuple(new_children)
        if len(self._children) == 1:
            [self.replacement] = self._children

    def __getitem__(self, index):
        start, end = _get_slice_indices(self, index)
        new_children = []
        for child in self._children:
            child_len = len(child)
            if end <= 0:
                break
            elif start >= child_len:
                pass
            else:
                if start <= 0 and end >= child_len:
                    new_children.append(child)
                else:
                    new_children.append(child[start:end])
            start -= child_len
            if start < 0:
                start = 0
            end -= child_len
        return Concat(*new_children)


class NamedContainer(Expression):
    """No-op unary expression

    Useful to show structure of complicated expressions
    in :func:`dump`-like tools.

    :param name: The name used in :meth:`pretty_name` and :func:`dump`
    :param val: An expression this evaluates to
    """
    def __init__(self, name, val):
        self._name = name
        self._val = val

    def get(self):
        return self._val.get()

    @property
    def pretty_name(self):
        return self._name

    @property
    def children(self):
        yield self._val


class Interpolation(Expression):
    """Evaluates to a weighted average of two expressions.

    :param a: Start expression, returned when t=0
    :param b: End expression, returned when t=1
    :param t: The weight

    The :token:`t` parameter must be a scalar (single-element) expression.

    Note that :token:`t` is not limited to [0..1]; extrapolation is possible.
    """
    def __init__(self, a, b, t):
        self._a, self._b = _coerce_all([a, b])
        self._t = _coerce(t, 1)
        if len(self._t) != 1:
            raise ValueError('Interpolation coefficient must be '
                             'a single number')
        self._a.replacement_available.connect(self._replace_a)
        self._b.replacement_available.connect(self._replace_b)
        self._t.replacement_available.connect(self._replace_t)

    def get(self):
        t = float(self._t)
        nt = 1 - t
        return tuple(a * nt + b * t for a, b in zip(self._a, self._b))

    def _replace_a(self):
        self._a = _replace_child(self._a, self._replace_a)

    def _replace_b(self):
        self._b = _replace_child(self._b, self._replace_b)

    def _replace_t(self):
        self._t = t = _replace_child(self._t, self._replace_t)
        if isinstance(t, Constant):
            if t == 0:
                self.replacement = simplify(self._a)
            elif t == 1:
                self.replacement = simplify(self._b)

    @property
    def children(self):
        yield NamedContainer('from', self._a)
        yield NamedContainer('to', self._b)
        yield NamedContainer('t', self._t)


class Progress(Expression):
    """Gives linear progress according to a Clock

    The value of this expression is
    0 at the start (``clock``'s current time + ``delay``),
    and 1 at the end (``duration`` time units after start).
    Between those two times, it changes smoothly as the clock advances.

    If ``clamp`` is true, the value stays 0 before the start and 1 after end.
    Otherwise, it is extrapolated: it will be negative before the start,
    and greater than 1 after the end.
    """
    def __init__(self, clock, duration, *, delay=0, clamp=True):
        self._clock = clock
        self._start = clock.time + float(delay)
        self._duration = float(duration)
        if self._duration == 0:
            raise ZeroDivisionError()
        self._clamp = clamp
        if clamp:
            clock.schedule(delay + duration, self._fix)

    def __len__(self):
        return 1

    def get(self):
        rv = (self._clock.time - self._start) / self._duration
        if self._clamp:
            if rv <= 0:
                return (0, )
            elif rv >= 1:
                return (1, )
        return (rv, )

    def _fix(self):
        self.replacement = Constant(1)
