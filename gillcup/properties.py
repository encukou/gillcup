"""Helper descriptors for using Expressions as object attributes

Gillcup's :mod:`~gillcup.expressions` work quite well when used as attributes
of objects.
For example, let's imagine a "Beeper" class that keeps track of a volume
and a pitch.
Treating the volume a numeric attribute works as expected, except
the value of Expression objects can be changed::

    >>> from gillcup.expressions import Constant, Value

    >>> class RawBeeper:
    ...     volume = Constant(0)
    ...     pitch = Constant(440)
    >>> raw_beeper = RawBeeper()
    >>> raw_beeper.volume
    <0.0>
    >>> raw_beeper.volume += 2
    >>> raw_beeper.volume
    <2.0>
    >>> val = Value(2)
    >>> raw_beeper.volume *= val
    >>> raw_beeper.volume
    <4.0>
    >>> val.set(21)
    >>> raw_beeper.volume
    <42.0>

However, with more advanced usage it becomes apparent that
for animated attributes, Python's normal
attribute/value mechanics can use some additional custom behavior.
For this reason, specific attributes of a class can be marked as an
:class:`AnimatedProperty`, which enables some this behavior:

* The value of an animated property is always an
  :class:`~gillcup.expressions.Expression` -- values assigned to it are run
  through :func:`~gillcup.expressions.coerce`,
  which converts any raw numbers and tuples.
* Animated properties simplify :ref:`linking <property-linking>`,
  that is, making one property's value depend on another.
* Animated properties support
  :ref:`vector and component properties <vector-properties>`.
  For example, for a `position` property, one can easily define `x` and `y`
  properties that will be kept in sync.

Animated properties are defined at the class level,
specifying their default value, and an optional name::

    >>> class Beeper:
    ...     volume = AnimatedProperty(name='volume')
    ...     pitch = AnimatedProperty(name='pitch',
    ...                              make_default=lambda inst: 440)
    >>> beeper = Beeper()
    >>> beeper.pitch
    <440.0>

.. note:: See the :ref:`Autonaming <property-autonaming>` section
          for a more convenient naming method.


It should be noted that, except for the additional features described here,
most of Python's normal attribute/value mechanics are preserved -- the example
at the beginning of this section runs fine with the ``Beeper`` class
instead of ``RawBeeper``.

The big caveat is that the expression retreived from
a :class:`AnimatedProperty` is *not* the exact Expression object
that was stored in it.
In the following example, we get an error because ``beeper.volume`` is not
a :class:`~gillcup.expressions.Value`::

    >>> beeper = Beeper()
    >>> beeper.volume = Value(20)
    >>> beeper.volume.set(50)
    Traceback (most recent call last):
        ...
    AttributeError: '_PropertyValue' object has no attribute 'set'

.. note:: The possibility of this happening is implied by the coercion step:
          :func:`~gillcup.expressions.coerce` can change the passed-in
          object to different (usually simplified) expression
          with the same value.
          AnimatedExpression goes a step further,
          and always uses its special expression type that,
          among other things, enables the linking functionality.

The upshot is: If you need to do anything with a custom Expression that is
not part of the :class:`Expression API <gillcup.expressions.Expression>`,
keep a reference to the Expression object itself in a simple variable.

Let's now look at :class:`AnimatedProperty` features in more depth.

Coercion
--------

The :class:`AnimatedProperty` calls :func:`~gillcup.expressions.coerce` on
values assigned to it, so any numbers or tuples are converted to expressions::

    >>> beeper.pitch = 880
    >>> beeper.pitch
    <880.0>
    >>> isinstance(beeper.pitch, Expression)
    True

Also, as part of coercion, animated properties check the size of whatever
is being assigned to the property::

    >>> beeper.pitch = 1, 2, 3
    Traceback (most recent call last):
        ...
    ValueError: Mismatched vector size: 3 != 1

.. note:: See :ref:`Vector and Component properties <vector-properties>`
          for info on properties that would accept the ``(1, 2, 3)`` tuple.

Expressions operations such as ``+`` or ``/`` already coerce their operands,
so augmented assignment (such as ``+=`` and ``/=``) work well with simple
Expression-valued attributes, even without AnimatedProperty's help,

On Expression identity and values
---------------------------------

In Python, when assigning the value of one property to another,
the properties are not linked together -- subsequent updates of the "source"
don't affect the "target" property::

    >>> source_beeper = RawBeeper()
    >>> target_beeper = RawBeeper()
    >>> source_beeper.volume = 50
    >>> target_beeper.volume = source_beeper.volume
    >>> target_beeper.volume
    50
    >>> source_beeper.volume = 10
    >>> target_beeper.volume
    50

Expressions work the same way, though because their value can change over time,
the mechanics may not be obvious at first.
In some ways, Expressions behave like mutable containers,
e.g. Python lists of values.

Assigning an Expression used in one Beeper to another Beeper makes
the two Beepers share the same Expression object.
Changes to the Expression's value are reflected on both objects::

    >>> source_beeper = RawBeeper()
    >>> target_beeper = RawBeeper()
    >>> volume_value = source_beeper.volume = Value(50)
    >>> target_beeper.volume = source_beeper.volume
    >>> source_beeper.volume, target_beeper.volume
    (<50.0>, <50.0>)
    >>> volume_value.set(80)
    >>> source_beeper.volume, target_beeper.volume
    (<80.0>, <80.0>)

When a new object is assigned, the properties are no longer linked in any way::

    >>> source_beeper.volume = Value(10)
    >>> source_beeper.volume, target_beeper.volume
    (<10.0>, <80.0>)

Things work exactly the same with :class:`AnimatedProperty`
(i.e. when we use ``Beeper`` instead of ``RawBeeper`` in the above example).

.. note:: As explained above, to call the
          :meth:`Value.set <gillcup.expressions.Value.set>`
          method, which is not part of the Expression API, we keep a reference
          to the original Value object in a simple variable.


There are two different possible behaviors for assignment,
which Gillcup supports, and which are consistent with how
simple numbers/tuples work:

1.  Use the current value of the expression, and stop all animations.
    This is achieved by converting the value to number::

        >>> target_beeper.volume = float(source_beeper.volume)

    Or, for vector properties, to a tuple::

        >>> target_beeper.volume = tuple(source_beeper.volume)

    (Converting to tuple works for single-valued expressions as well,
    for consistency, but it is somewhat less obvious.)

    This will assign a :class:`~gillcup.expressions.Constant` to the property.

2.  Link the values together, so that any updates to the source are reflected
    in the target.
    This is discussed in the next section.

.. _property-linking:

Linking
-------

To "link" one property to another, call the :func:`link` function
on the "source" property::

    >>> source_beeper = Beeper()
    >>> target_beeper = Beeper()
    >>> source_beeper.volume = 50
    >>> target_beeper.volume = link(source_beeper.volume)
    >>> source_beeper.volume, target_beeper.volume
    (<50.0>, <50.0>)

    >>> source_beeper.volume = 40
    >>> source_beeper.volume, target_beeper.volume
    (<40.0>, <40.0>)

Calling :func:`link` creates an expression that evaluates attribute access
of the property.
This result can be used in more complicated expressions::

    >>> target_beeper.volume = link(source_beeper.volume) * 2
    >>> source_beeper.volume, target_beeper.volume
    (<40.0>, <80.0>)

    >>> source_beeper.volume += 2
    >>> source_beeper.volume, target_beeper.volume
    (<42.0>, <84.0>)

Note that :func:`link` only works on property values, i.e. expressions that
result directly from property attribute access.
Other expressions cannot be linked::

    >>> link(source_beeper.volume * 2)
    Traceback (most recent call last):
        ...
    TypeError: <class '...'> can't be linked

Beware that you can create loops by making a property's value depend
on itself (possibly indirectly).
The infinite recursion will result in a :class:`RuntimeError` being raised
when the value is accessed (or even earlier)::

    >>> source_beeper.volume = link(source_beeper.volume)
    >>> int(source_beeper.volume)
    Traceback (most recent call last):
        ...
        ...
        ...
    RuntimeError: maximum recursion depth exceeded ...

.. TODO: document the link method of property values... (or get rid of it?)

.. _vector-properties:

Vector and Component properties
-------------------------------

Gillcup supports expressions with more than one element, such as a 3D
*position* with *x*, *y*, and *z* coordinates.
It is easy to define properties for both the vector proprerty
and its individual components::

    >>> class Point3D:
    ...     pos = x, y, z = AnimatedProperty(3, name='pos: x y z')

Note the shorthand syntax for naming all the properties
(but see the :ref:`Autonaming <property-autonaming>` section
for a more convenient naming method).

The component properties defined this way are synchronized
with their parent vector::

    >>> point = Point3D()
    >>> point.pos
    <0.0, 0.0, 0.0>
    >>> point.x
    <0.0>
    >>> point.pos = 10, 20, 30
    >>> point.x
    <10.0>
    >>> point.x += 32
    >>> point.pos
    <42.0, 20.0, 30.0>

.. _property-autonaming:

Autonaming
----------

The :func:`autoname` decorator, when applied to a class,
names all its animated properties according to the attribute name they
are assigned to.
This means you can avoid repeating the name,
and still have the properties named for easier debugging::

    >>> @autoname
    ... class Buzzer3D:
    ...     volume = AnimatedProperty()
    ...     pitch = AnimatedProperty(make_default=lambda s: 440)
    ...     pos = x, y, z = AnimatedProperty(3)

    >>> Buzzer3D.volume.name
    'volume'
    >>> Buzzer3D.pos.name
    'pos'
    >>> Buzzer3D.x.name
    'x'


Reference
---------

.. autoclass:: AnimatedProperty
.. autofunction:: link
.. autofunction:: autoname

"""

import re
import weakref

from gillcup.expressions import Expression, coerce, simplify
from gillcup.animations import anim
from gillcup.util.autoname import autoname as _autoname, autoname_property


def autoname(cls):
    """Class decorator that automatically names properties

    Every AnimatedProperty defined directly on the decorated class
    has its name set to the atribute name it is bound to.

    See the :ref:`Autonaming <property-autonaming>` section
    of the documentation for discussion.
    """
    return _autoname(cls)


@autoname_property('name')
class AnimatedProperty:
    """Descriptor for Expression-valued properties.

    :param int size: The size of the expression.
    :param make_default: A function that, when called with the object
                         this property is on,
                         returns the default value of the expression.

                         The result will be
                         :func:`coerced <gillcup.expressions.coerce>`.

                         If not given, the default will be zeros.
    :param str name: The name of this property, which should be a valid
                     Python identifier.

                     For vector properties, the name can be given as
                     ``'vector_name: comp_name1 comp_name2 comp_name3'``,
                     where ``vector_name`` names the property itself and
                     ``comp_nameN`` names its Nth component.
                     Whitespace around ``:`` is optional.
                     Component names may be separated by commas
                     and/or whitespace.
    :param str doc: An optional docstring.

    .. autospecialmethod:: __iter__
    """
    def __init__(self, size=1, make_default=None, *, name=None, doc=None):
        self._instance_expressions = {}
        if make_default:
            self._size = size
            self._factory = make_default
        else:
            self._size = size
            default = coerce(0, size=size)
            self._factory = lambda instance: default

        self.name, component_names = _get_names(name, size)

        self._components = tuple(_ComponentProperty(self, i, name)
                                 for i, name in enumerate(component_names))
        self.__doc__ = doc

    def __len__(self):
        return self._size

    def __iter__(self):
        """Yield components of this property

        Note that this is called when iterating the *descriptor itself*, e.g.::

            >>> class Sprite2D:
            ...     position = x, y = AnimatedProperty(2)

        The values of the components are synchronized with their parent
        (*self* in this case).

        The component descriptors have the same interface as
        :class:`AnimatedProperty`, except they lack ``__iter__``.
        """
        yield from self._components

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        else:
            try:
                exp = self._instance_expressions[id(instance)]
            except KeyError:
                exp = coerce(self._factory(instance), size=self._size)
            return _PropertyValue(self, instance, exp)

    def __set__(self, instance, value):
        exp = coerce(value, size=self._size)
        if id(instance) not in self._instance_expressions:
            weakref.finalize(instance, self._instance_expressions.pop,
                             id(instance), None)
        self._instance_expressions[id(instance)] = simplify(exp)


def _get_names(name, size):
    component_names = None
    if name:
        name, sep, component_names_str = name.partition(':')
        if sep:
            name = name.strip()
            component_names = re.split(r'\s+(?!,)|\s*,\s*',
                                       component_names_str.strip())
            if len(component_names) != size:
                raise ValueError(
                    'Bad number of component names: {} != {}: {}'.format(
                        len(component_names), size, component_names))

    if not name:
        name = '<unnamed property>'

    if not component_names:
        component_names = ['{}[{}]'.format(name, i) for i in range(size)]

    return name, component_names


def link(prop):
    """Given a property value, returns an expression linked to that value

    See the :ref:`Linking <property-linking>` section of the documentation
    for a discussion.
    """
    try:
        func = prop._gillcup_propexp_link
    except AttributeError:
        raise TypeError("{} can't be linked".format(type(prop)))
    else:
        return func()


def _link_method(self, source):
        linked = link(source)
        self._prop.__set__(self._instance, linked)


def _anim_method(self, target, duration=0, clock=None, *,
                 delay=0, easing=None, infinite=False, strength=1):
        instance = self._instance
        if clock is None:
            try:
                clock = instance.clock
            except AttributeError:
                raise TypeError('{} does not have a clock. '
                                'Pass a clock to anim() explicitly.'.format(
                                    instance))
        animation = anim(
            start=self.replacement,
            end=target,
            duration=duration,
            clock=clock,
            delay=delay,
            easing=easing,
            infinite=infinite,
            strength=strength,
        )
        self._prop.__set__(instance, animation)


class _PropertyValue(Expression):
    def __init__(self, prop, instance, expression):
        self._prop = prop
        self._instance = instance
        self.replacement = simplify(expression)

    def get(self):
        return self.replacement.get()

    @property
    def pretty_name(self):
        return '{0!r}.{1} value'.format(self._instance, self._prop.name)

    @property
    def children(self):
        yield self.replacement

    def _gillcup_propexp_link(self):
        return _Linked(self._prop, self._instance)

    link = _link_method
    anim = _anim_method


class _Linked(Expression):
    def __init__(self, prop, instance):
        self._prop = prop
        self._instance = instance

    def get(self):
        return self._prop.__get__(self._instance).get()

    @property
    def pretty_name(self):
        return 'linked {0!r}.{1}'.format(self._instance, self._prop.name)

    @property
    def children(self):
        yield simplify(self._prop.__get__(self._instance))

    def _gillcup_propexp_link(self):
        return self


@autoname_property('name')
class _ComponentProperty:
    def __init__(self, parent, index, name):
        self._parent = parent
        self._index = index
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        else:
            exp = self._parent.__get__(instance, owner)
            return _ComponentPropertyValue(self, self._parent, instance, exp,
                                           self._index)

    def __set__(self, instance, value):
        exp = self._parent.__get__(instance)
        new = exp.replace(self._index, coerce(value, size=1))
        self._parent.__set__(instance, new)


class _ComponentPropertyValue(Expression):
    def __init__(self, prop, parent, instance, expression, index):
        self._prop = prop
        self._parent = parent
        self._instance = instance
        self._index = index
        self.replacement = simplify(expression[self._index])

    def get(self):
        return self.replacement.get()

    @property
    def pretty_name(self):
        return '{0!r}.{1} ({2}[{3}]) value'.format(self._instance,
                                                   self._prop.name,
                                                   self._parent.name,
                                                   self._index)

    @property
    def children(self):
        yield self._parent.__get__(self._instance)

    def _gillcup_propexp_link(self):
        return _LinkedComponent(self._prop, self._parent, self._instance,
                                self._index)

    link = _link_method
    anim = _anim_method


class _LinkedComponent(Expression):
    def __init__(self, prop, parent, instance, index):
        self._prop = prop
        self._parent = parent
        self._instance = instance
        self._index = index

    def get(self):
        return (self._parent.__get__(self._instance).get()[self._index], )

    @property
    def pretty_name(self):
        return 'linked {0!r}.{1} ({2}[{3}])'.format(self._instance,
                                                    self._prop.name,
                                                    self._parent.name,
                                                    self._index)

    @property
    def children(self):
        yield self._parent.__get__(self._instance)

    def _gillcup_propexp_link(self):
        return self
