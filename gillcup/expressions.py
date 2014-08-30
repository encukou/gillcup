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
Operations such as addition are element-wise
(``<1, 2> + <3, 4>`` results in ``<4, 6>``).
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

    >>> bool(exp)
    True

Like arithmetic operations, comparisons are element-wise,
``(<1, 2> == <1, 3>)`` results in ``<False, True>``.
Comparisons with more than one element cannot be converted directly to
a single boolean; you need to use Python's :func:`all` or :func:`any`
functions to check them:

    >>> if all(Constant(1, 2, 3) == Constant(1, 2, 3)):
    ...     print('yes, they are equal')
    yes, they are equal
    >>> if any(Constant(1, 1, 1) > Constant(100, 200, 0)):
    ...     print('yes, some are larger')
    yes, some are larger

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


Expression invariants
---------------------

These invariants are assumed:

* The size (as determined by :func:`len`) of every Expression is constant
  throughout the Expression's lifetime.
* For any Expression ``exp``, the simplified Expression (``exp.replacement``)
  has the same value as ``exp``
* While any Expression is being evaluated, the value of any (other) Expression
  stays constant.


Reference
---------

.. autoclass:: gillcup.expressions.Expression

Basic Expressions
.................

.. autoclass:: gillcup.expressions.Constant
.. autoclass:: gillcup.expressions.Value
.. autoclass:: gillcup.expressions.Progress

Compound Expressions
....................

.. autoclass:: gillcup.expressions.Reduce
.. autoclass:: gillcup.expressions.Elementwise
.. autoclass:: gillcup.expressions.Interpolation
.. autoclass:: gillcup.expressions.Box

Arithmetic Expressions
~~~~~~~~~~~~~~~~~~~~~~

For the following, using the appropriate operator is preferred
to constructing them directly:

.. autoclass:: gillcup.expressions.Sum
.. autoclass:: gillcup.expressions.Product
.. autoclass:: gillcup.expressions.Difference
.. autoclass:: gillcup.expressions.Quotient
.. autoclass:: gillcup.expressions.Neg
.. autoclass:: gillcup.expressions.Compare

.. autoclass:: gillcup.expressions.Slice
.. autoclass:: gillcup.expressions.Concat

Debugging helpers
.................

.. autofunction:: gillcup.expressions.dump


Helpers
.......

.. autofunction:: gillcup.expressions.simplify
.. autofunction:: gillcup.expressions.coerce
.. autofunction:: gillcup.expressions.safediv

"""

import operator
import functools
import itertools
import math

from gillcup.signals import signal


def simplify(exp):
    """Return a simplified version the given expression

    Let's use :class:`Sum` as an example expression.
    The Sum keeps a list of the expressions it adds together:

        >>> val = Sum([Value(1), Value(2), Value(3)])
        >>> print(dump(val))
        + <6.0>:
          Value <1.0>
          Value <2.0>
          Value <3.0>

    Usually, expressions are simplified automatically.
    For example, if the Sum expression is given constants,
    it adds them together directly:

        >>> val = Sum([1, 2, 3])
        >>> print(dump(val))
        + <6.0>:
          Constant <6.0>

    Calling :func:`simplify` is not needed to get this kind of simplification.

    However, some expressions can be simplified even further:
    this Sum can just be entirely replaced with the constant.
    However, we cannot really change the types of objects,
    so in this case we have the Sum signal that it can be replaced
    with a simpler expression::

        >>> simplified = simplify(val)
        >>> print(dump(simplified))
        Constant <6.0>

    If the expression cannot be simplified, :func:`simplify` simply returns
    the original unchanged:

        >>> print(dump(simplify(Value(1))))
        Value <1.0>

    Some expressions can be simplified at some time after initialization,
    for example after calling :meth:`Value.fix` or when a :class:`Progress`
    reaches its end time.
    When this happens, the expression's
    :meth:`~Expression.replacement_available` signal is triggered,
    and :func:`simplify` will start returning the new replacement.
    """
    return exp.replacement


def coerce(value, *, size=None, strict=True):
    """Turn an Expression, constant, or number into an Expression

    :param value: The value to be coerced
    :param size: The size of the resulting expression
    :param strict: If true, output size is enforced.

    ..

        >>> coerce([1, 2, 3])
        <1.0, 2.0, 3.0>
        >>> coerce(Value(1, 2, 3))
        <1.0, 2.0, 3.0>

    If an Expression is given, it is simplified (see :meth:`simplify`).


    If :token:`strict` is true, and :token:`size` is given, the size of
    input expressions and iterable values is checked::

        >>> coerce((1, 2), size=3)
        Traceback (most recent call last):
          ...
        ValueError: Mismatched vector size: 2 != 3

        >>> coerce((1, 2), size=3, strict=False)
        <1.0, 2.0>

    Numeric inputs are repeated :token:`size` times
    (regardless of :token:`strict`)::

        >>> coerce(2)
        <2.0>
        >>> coerce(2, size=3)
        <2.0, 2.0, 2.0>
    """
    try:
        value.get  # See if this quacks like an Expression
    except AttributeError:
        tup = _nonexpression_as_tuple(value, size, strict)
        return Constant(*tup)
    else:
        if strict and size is not None:
            _check_len(value, size)
        return simplify(value)


class Expression:
    """A dynamic numeric value.

    This is a base class, subclass it but do not use it directly.

    Subclassing reference:

        Overridable members:

            .. automethod:: get
            .. autoattribute:: children
            .. autoattribute:: pretty_name

        Replacing:

            See :func:`simplify` for details on simplification.

            To request replacement, store the simplified expression in the
            :attr:`replacement` attribute.
            This will automatically trigger the :meth:`replacement_available`
            signal.

            Note that the original expression must continue to match the
            replacement even after this request is made.

            A compound expression should listen on the replacement_available
            signal of its components, so it can update itself when they are
            simplified.

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

                Return an Expression that compares the this expression
                element-wise to :token:`other`.

                The resing is an expression whose elements can be 0 or 1.

        .. function:: self + other
                      self - other
                      self * other
                      self / other

                *a.k.a.* :token:`__add__(other)` etc.

                Return a nes Expression that evaluates an element-wise
                operation on two values.

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

    def __bool__(self):
        size = len(self)
        if size == 1:
            return bool(float(self))
        elif size == 0:
            return False
        else:
            raise ValueError('using a vector as a boolean is ambiguous; '
                             'use `all` or `any` to clarify')

    def __repr__(self):
        try:
            value = tuple(self)
        except Exception as e:
            return '<%s while getting value>' % type(e).__name__
        return '<{}>'.format(', '.join(str(n) for n in value))

    def get(self):
        """Return the current value of this expression, as a tuple.

        This method should be kept free of side effects; in particular,
        it may not change (even indirectly) the value of any other
        Expression.
        """
        raise NotImplementedError()

    @property
    def replacement(self):
        """A simplified version of this expression

        If a simplified version does not exist, the value is self.
        """
        try:
            replacement = self.__replacement
        except AttributeError:
            return self
        else:
            while True:
                try:
                    replacement = replacement.__replacement
                except AttributeError:
                    self.__replacement = replacement
                    return replacement

    @replacement.setter
    def replacement(self, new_exp):
        if new_exp is not self.replacement:
            self.__replacement = new_exp
            self.replacement_available()

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
        return simplify(Compare([self, other], operator.eq, '='))

    def __ne__(self, other):
        return simplify(Compare([self, other], operator.ne, '≠'))

    def __lt__(self, other):
        return simplify(Compare([self, other], operator.lt, '<'))

    def __gt__(self, other):
        return simplify(Compare([self, other], operator.gt, '>'))

    def __le__(self, other):
        return simplify(Compare([self, other], operator.le, '≤'))

    def __ge__(self, other):
        return simplify(Compare([self, other], operator.ge, '≥'))

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
        return simplify(Neg(self))

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
        replacement = coerce(replacement, size=stop - start, strict=False)
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

    The dumper deals with repeated expressions using YAML-style markers:

        >>> exp = Value(3, 3, 3) + 3
        >>> exp = exp / exp
        >>> print(dump(exp))
        / <1.0, 1.0, 1.0>:
          + <6.0, 6.0, 6.0>:  (&1)
            Value <3.0, 3.0, 3.0>
            Constant <3.0, 3.0, 3.0>
          + <6.0, 6.0, 6.0>  (*1)

        >>> exp = Value(3, 3, 3)
        >>> print(dump(exp + exp + exp))
        + <9.0, 9.0, 9.0>:
          Value <3.0, 3.0, 3.0>  (&1)
          Value <3.0, 3.0, 3.0>  (*1)
          Value <3.0, 3.0, 3.0>  (*1)

    Expressions are encouraged to "lie" about their structure in
    :attr:`~Expression.children`, if it leads to better readibility.
    For example, an expression with several heterogeneous children
    can wrap each child in a :class:`Box`::

        >>> exp = Interpolation(Value(0), Value(10), Value(0.5))
        >>> print(dump(exp))
        Interpolation <5.0>:
          start <0.0>:
            Value <0.0>
          end <10.0>:
            Value <10.0>
          t <0.5>:
            Value <0.5>

    Here the ``start``, ``end``, and ``t`` are dynamically generated
    :class:`Box` expressions whose only purpose is to provide the name to make
    the dump more readable.
    """

    # Value of next marker to be assigned
    counter = 1

    # Memo of all exps seen so far, keyed by id(exp)
    # a value of None → seen only once (don't print a marker)
    # a number → print the number as a marker
    memo = {}

    def gen(exp, indent):
        """Generate the lines of the dump

        Yields records suitable for fmt() below, tuples of:
        - indent: the indentation level, as int
        - exp: the expression itself
        - sigil: '&' if this is the first time we see this exp, '*' otherwise
            (this is used in the YAML-style markers: '&' means definition,
            '*' is reference)
        - children_follow: True if exp's children are listed after this line.
            If exp has no children, this is False
            (used to display ':' if an indented block follows)
        """
        nonlocal counter
        try:
            # Have we seen exp before?
            entry = memo[id(exp)]
        except KeyError:
            # No! Record it, and yield it, along with any children
            memo[id(exp)] = None
            children = list(exp.children)
            yield indent, exp, '&', bool(children)
            for child in children:
                yield from gen(child, indent + 1)
        else:
            # Yes! Yield it, but don't bother listing children again
            yield indent, exp, '*', False
            # If this is the second (but not third, etc.) time we've seen it,
            # assign a marker value
            if entry is None:
                memo[id(exp)] = counter
                counter += 1

    # Running exp() to exhaustion will fill up `memo`
    entries = list(gen(exp, 0))

    def fmt(indent, exp, sigil, children_follow):
        """Format a single line of the dump

        See gen() for the input
        """
        marker = memo.get(id(exp))
        if marker is None:
            postfix = ''
        else:
            postfix = '  (%s%s)' % (sigil, marker)
        return '{indent}{exp.pretty_name} {exp}{colon}{postfix}'.format(
            indent='  ' * indent,
            exp=exp,
            colon=':' if children_follow else '',
            postfix=postfix,
        )

    return '\n'.join(fmt(*entry) for entry in entries)


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


def _nonexpression_as_tuple(value, size=None, strict=True):
    try:
        iterator = iter(value)
    except TypeError:
        if size is None:
            return (float(value), )
        else:
            return (float(value), ) * size
    else:
        result = tuple(float(v) for v in iterator)
        if strict and size is not None:
            _check_len(result, size)
        return result


def _as_tuple(value, size=None):
    try:
        get = value.get
    except AttributeError:
        return _nonexpression_as_tuple(value, size)
    else:
        if size is not None:
            _check_len(value, size)
        return get()


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
        if self.replacement is self:
            value = tuple(float(v) for v in value)
            if len(value) != self._size:
                raise ValueError('Mismatched vector size: {} != {}'.format(
                    len(value), self._size))
            self._value = value
        else:
            raise ValueError('value has been fixed')

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
    return tuple(coerce(e, size=size) for e in exps)


def _reduce_tuples(operands, op):
    reducer = functools.partial(functools.reduce, op)
    return tuple(map(reducer, zip(*operands)))


def _check_len_match(a, b):
    if len(a) != len(b):
        raise ValueError('Mismatched vector size: {} != {}'.format(
            len(a), len(b)))


def _check_len(exp, expected):
    if len(exp) != expected:
        raise ValueError('Mismatched vector size: {} != {}'.format(
            len(exp), expected))


class Reduce(Expression):
    """Applies a :func:`reduce <functools.reduce>` operation
    element-wise on a number of Expressions.

    Assumes the `op` function is pure, and takes number of arguments equal
    to the number of operands.

    All operands must be the same size.

    Class attributes:

        .. attribute:: commutative

            True to enable optimizations that assume `op` implements a
            commutative operator

        .. attribute:: identity_element

            If not None, gives the number that can be ignored for this
            operation (or if :token:`commutative` is true, the number that
            can be ignored if it's not the first operand).
            For example, 0 for ``+`` or ``-``, 1 for ``*`` or ``/``.
    """
    commutative = False
    identity_element = None

    def __init__(self, operands, op):
        self._op = op
        self._operands = tuple(_coerce_all(operands))
        first = self._operands[0]
        for operand in self._operands[1:]:
            _check_len_match(operand, first)
        for i, oper in enumerate(self._operands):
            oper.replacement_available.connect(self._replace_operands)
        self._replace_operands()

    def get(self):
        return _reduce_tuples(self._operands, self._op)

    def __len__(self):
        return len(self._operands[0])

    @property
    def pretty_name(self):
        return '{}({})'.format(type(self).__name__, self._op)

    @property
    def children(self):
        return self._operands

    def _replace_operands(self, commutative=False):
        new = []
        size = len(self._operands[0])

        def _generate_operands(operands):
            for i, oper in enumerate(operands):
                oper = _replace_child(oper.replacement, self._replace_operands)
                if ((self.commutative or i == 0) and
                        type(oper) == type(self) and
                        oper._op == self._op):
                    yield from _generate_operands(oper._operands)
                else:
                    yield oper

        for oper in _generate_operands(self._operands):
            if (new and isinstance(oper, Constant) and
                    (self.commutative or len(new) == 1) and
                    isinstance(new[-1], Constant)):
                new[-1] = Constant(*tuple(map(self._op,
                                              tuple(new[-1]),
                                              tuple(oper))))
            else:
                new.append(oper)
            if (new and isinstance(oper, Constant) and
                    (self.commutative or len(new) > 1) and
                    all(x == self.identity_element for x in new[-1])):
                new.pop()
        if not new:
            new.append(Constant(*[self.identity_element] * size))
        self._operands = new
        if len(self._operands) == 1:
            [self.replacement] = self._operands


class Sum(Reduce):
    """Element-wise sum
    """
    pretty_name = '+'
    commutative = True
    identity_element = 0

    def __init__(self, operands):
        super().__init__(operands, operator.add)

    def _dump_name(self):
        return '+'


class Product(Reduce):
    """Element-wise product
    """
    pretty_name = '*'
    commutative = True
    identity_element = 1

    def __init__(self, operands):
        super().__init__(operands, operator.mul)


class Compare(Reduce):
    """Element-wise comparison
    """
    @property
    def pretty_name(self):
        return '`{}`'.format(self._symbol)

    def __init__(self, operands, op, symbol):
        super().__init__(operands, op)
        self._symbol = symbol


class Difference(Reduce):
    """Element-wise difference
    """
    pretty_name = '-'
    identity_element = 0

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
    """Element-wise quotient

    Division by zero will result in NaN or infinity, rather than raising
    an exception -- see :func:`safediv`.
    """
    pretty_name = '/'
    identity_element = 1

    def __init__(self, operands):
        super().__init__(operands, safediv)


class Elementwise(Expression):
    """Applies a function element-wise on a single Expression.

    Assumes the `op` function is pure.
    """
    def __init__(self, operand, op):
        self._operand = coerce(operand)
        self._op = op
        self._operand.replacement_available.connect(self._replace_operand)
        self._replace_operand()

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

    Typical result of an ``exp[start:stop]`` operation
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
        else:
            source.replacement_available.connect(self._replace_source)
            self._replace_source()

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
        elif isinstance(src, Slice):
            self._source = src._source
            self._start = self._start + src._start
            self._stop = self._stop + src._start
        elif isinstance(src, Concat):
            start = self._start
            new_children = []
            children_iter = iter(list(src._children))
            for child in children_iter:
                if start > len(child):
                    start -= len(child)
                else:
                    if start:
                        first_child = child[start:]
                    else:
                        first_child = child
                    break
            else:
                raise AssertionError('out of children (at start)')
            length_remaining = self._len
            for child in itertools.chain([first_child], children_iter):
                if not length_remaining:
                    break
                assert length_remaining > 0
                if length_remaining > len(child):
                    new_children.append(child)
                    length_remaining -= len(child)
                else:
                    new_children.append(child[:length_remaining])
                    break
            else:
                raise AssertionError('out of children (at end)')
            self.replacement = Concat(*new_children)


class Concat(Expression):
    """Concatenation of several Expressions.

    >>> Concat(Constant(1, 2), Constant(3))
    <1.0, 2.0, 3.0>

    Usually created as a result of :meth:`~Expression.replace`.
    """
    def __init__(self, *children):
        children_gen = (coerce(c) for c in children)
        self._children = tuple(c for c in children_gen if len(c))
        self._len = sum(len(c) for c in self._children)
        self._simplify_children()
        for child in self._children:
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
            elif (isinstance(child, Slice) and
                    new_children and
                    isinstance(new_children[-1], Slice) and
                    child._source is new_children[-1]._source and
                    child._start == new_children[-1]._stop):
                new_index = slice(new_children[-1]._start, child._stop)
                new_children[-1] = simplify(Slice(child._source, new_index))
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


class Box(Expression):
    """Mutable container expression

    Proxies to another Expression.

    :param name: The name used in :meth:`pretty_name` and :func:`dump`
    :param value: An expression this evaluates to.
                  May be changed after creation by setting the
                  :attr:`value` attribute.

    Also useful to show structure of complicated expressions when debugging,
    see :func:`dump` for an example.
    """
    def __init__(self, name, value):
        self._name = name
        self.value = value

    def get(self):
        return self.value.get()

    @property
    def pretty_name(self):
        return self._name

    @property
    def children(self):
        yield self.value


class Interpolation(Expression):
    """Evaluates to a weighted average of two expressions.

    :param a: Start expression, returned when t=0
    :param b: End expression, returned when t=1
    :param t: The weight

    The :token:`t` parameter must be a scalar (single-element) expression.

    Note that :token:`t` is not limited to [0..1]; extrapolation is possible.
    """
    def __init__(self, start, end, t):
        self._start, self._end = _coerce_all([start, end])
        self._t = coerce(t, size=1)
        if len(self._t) != 1:
            raise ValueError('Interpolation coefficient must be '
                             'a single number')
        self._start.replacement_available.connect(self._replace_start)
        self._end.replacement_available.connect(self._replace_end)
        self._t.replacement_available.connect(self._replace_t)
        self._replace_t()
        self._replace_const_to_const()

    def get(self):
        t = float(self._t)
        nt = 1 - t
        return tuple(a * nt + b * t for a, b in zip(self._start, self._end))

    def _replace_start(self):
        self._start = _replace_child(self._start, self._replace_start)
        self._replace_const_to_const()

    def _replace_end(self):
        self._end = _replace_child(self._end, self._replace_end)
        self._replace_const_to_const()

    def _replace_t(self):
        self._t = t = _replace_child(self._t, self._replace_t)
        if isinstance(t, Constant):
            if t == 0:
                self.replacement = simplify(self._start)
            elif t == 1:
                self.replacement = simplify(self._end)

    def _replace_const_to_const(self):
        if (isinstance(self._start, Constant) and
                isinstance(self._end, Constant) and
                all(self._start == self._end)):
            self.replacement = self._start

    @property
    def children(self):
        yield Box('start', self._start)
        yield Box('end', self._end)
        yield Box('t', self._t)


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
