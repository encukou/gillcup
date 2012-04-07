# Encoding: UTF-8
"""Gillcup's Animated Properties

To animate Python objects, we need to change values of their attributes over
time.
There are two kinds of changes we can make: *discrete* and *continuous*.
A discrete change happens at a single point in time: for example, an object
is shown, some output is written, a sound starts playing.
:mod:`Actions <gillcup.actions>` are used for effecting
discrete changes.

Continuous changes happen over a period of time: an object smoothly moves
to the left, or a sound fades out.
These changes are made by animating special properties on objects.

Gillcup uses Python's `descriptor interface
<http://docs.python.org/howto/descriptor.html>`_ to provide efficient
animated properties.

Assigment to an animated attribute causes the property to get set to the given
value and cancels any running animations on it.

See :mod:`gillcup.animation` for information on how to actually do animations.
"""

from __future__ import unicode_literals, division, print_function

from gillcup.effect import Effect, ConstantEffect


class AnimatedProperty(object):
    """A scalar animated property

    Define animated properties as follows::

        class Tone(object):
            pitch = AnimatedProperty(440)
            volume = AnimatedProperty(0)

    Now, Tone instances will have `pitch` and `volume` set to the corresponding
    defaults, and can be animated.

    The **docstring** argument becomes the property's ``__doc__`` attribute.
    """
    def __init__(self, default, docstring=None):
        self.default = default
        if docstring:
            self.__doc__ = docstring

    def adjust_value(self, values):
        """Convert an animation's ``*args`` values into a property value

        For scalar properties, this converts a 1-tuple into its only element
        """
        [value] = values
        return value

    def get_target_property(self):
        """Return a property used for a dynamic animation's target
        """
        # Since AnimatedProperty doesn't care about its name, we can just
        # reuse it
        return self

    def __get__(self, instance, owner):
        if instance:
            return self.get_effect(instance).value
        else:
            return self

    def __set__(self, instance, value):
        self.animate(instance, ConstantEffect(value))

    def __delete__(self, instance):
        self.animate(instance, ConstantEffect(self.default))

    def get_effect(self, instance):
        """Get the current effect; possibly create a default one beforehand"""
        # pylint: disable=W0212
        try:
            effects = instance.__gillcup_effects
        except AttributeError:
            effects = instance.__gillcup_effects = {}
        try:
            effect = effects[self]
        except KeyError:
            effect = effects[self] = ConstantEffect(self.default)
        return effect

    def animate(self, instance, animation):
        """Set a new effect on this property; return the old one"""
        # pylint: disable=W0212
        parent = self.get_effect(instance)
        instance.__gillcup_effects[self] = animation
        return parent

    def do_replacements(self, instance):
        """Possibly replace current effect w/ a more lightweight equivalent"""
        # pylint: disable=W0212
        try:
            effects = instance.__gillcup_effects
            current_effect = effects[self]
        except (AttributeError, KeyError):
            pass
        else:
            effects[self] = current_effect.get_replacement()

    def tween_values(self, function, parent_value, value):
        """Call a scalar tween function on two values.
        """
        return function(parent_value, value)


class TupleProperty(AnimatedProperty):
    """A tuple animated property

    Iterating the TupleProperty itself yields sub-properties that can be
    animated individually.
    The intended idiom for declaring a tuple property is::

        x, y, z = position = TupleProperty(0, 0, 0)
    """
    def __init__(self, *default, **kwargs):
        super(TupleProperty, self).__init__(default, **kwargs)
        self.size = len(default)
        self.subproperties = [_TupleElementProperty(self, i)
                for i in range(self.size)]

    def adjust_value(self, value):
        """Convert an animation's ``*args`` values into a property value

        For tuple properties, return the tuple unchanged
        """
        return value

    def __set__(self, instance, value):
        self.animate(instance, ConstantEffect(self.adjust_value(value)))

    def __iter__(self):
        return iter(self.subproperties)

    def tween_values(self, function, parent_value, value):
        """Call a scalar tween function on two values.

        Calls the function on corresponding pairs of elements, returns
        the tuple of results
        """
        return tuple(map(function, parent_value, value))


class _TupleElementProperty(AnimatedProperty):
    """Animated property for one element of a TupleProperty
    """
    def __init__(self, parent, index):
        super(_TupleElementProperty, self).__init__(parent.default[index])
        self.parent = parent
        self.index = index

    def get_effect(self, instance):
        parent_effect = self.parent.get_effect(instance)
        return _TupleExtractEffect(parent_effect, self.index)

    def animate(self, instance, animation):
        tuple_effect = _TupleMakeEffect(animation, self.index)
        parent = self.parent.animate(instance, tuple_effect)
        tuple_effect.previous = parent
        return _TupleExtractEffect(parent, self.index)


class _TupleExtractEffect(Effect):
    """Effect that extracts one element of a tuple
    """
    def __init__(self, parent, index):
        super(_TupleExtractEffect, self).__init__()
        self.parent = parent
        self.index = index

    @property
    def value(self):
        """Value to be used for the property this effect is on"""
        return self.parent.value[self.index]


class _TupleMakeEffect(Effect):
    """Effect that recombines one changed element of a tuple with the rest

    `parent` is an Effect whose `value` is used for the changed element

    The `previous` attribute has the Effect with the original, full tuple.
    This attribute must be set after instantiation.
    """
    previous = None

    def __init__(self, parent, index):
        super(_TupleMakeEffect, self).__init__()
        self.parent = parent
        self.index = index

    @property
    def value(self):
        """Value to be used for the property this effect is on"""
        parent = self.parent
        return tuple(parent.value if i == self.index else val
            for i, val in enumerate(self.previous.value))


class ScaleProperty(TupleProperty):
    """A TupleProperty used for scales or sizes in multiple dimensions

    It acts as a regular TupleProperty, but supports scalars or short tuples in
    assignment or animation.

    Instead of a default value, __init__ takes the number of dimensions;
    the default value will be ``(1,) * num_dimensions``.

    If a scalar, or a tuple with only one element, is given, the value is
    repeated across all dimensions.
    If another short tuple is given, the remaining dimensions are set to 1.

    For example, given::

        width, height, length = size = ScaleProperty(3)

    the following pairs are equivalent::

        obj.size = 2
        obj.size = 2, 2, 2

        obj.size = 2, 3
        obj.size = 2, 3, 1

        obj.size = 2,
        obj.size = 2, 2, 2

    Similarly, ``Animation(obj, 'size', 2)`` is equivalent to
    ``Animation(obj, 'size', 2, 2, 2)``.
    """
    def __init__(self, num_dimensions, **kwargs):
        super(ScaleProperty, self).__init__(*(1, ) * num_dimensions, **kwargs)

    def adjust_value(self, value):
        """Expand the given tuple or scalar to a tuple of len=num_dimensions
        """
        try:
            size = len(value)
        except TypeError:
            return (value, ) * self.size
        if size == self.size:
            return value
        elif size == 1:
            return value * self.size
        elif size < self.size:
            return value + (1, ) * (self.size - size)
        else:
            raise ValueError('Too many dimensions for ScaleProperty')


class VectorProperty(TupleProperty):
    """A TupleProperty used for vectors

    It acts as a regular TupleProperty, but supports short tuples in
    assignment or animation by setting all remaining dimensions to 0.

    Instead of a default value, __init__ takes the number of dimensions;
    the default value will be ``(0,) * num_dimensions``.

    For example, given::

        x, y, z = position = VectorProperty(3)

    the following pairs are equivalent::

        obj.position = 2, 3
        obj.position = 2, 3, 0

        obj.position = 2,
        obj.position = 2, 0, 0

    Similarly, ``Animation(obj, 'position', 1, 2)`` is equivalent to
    ``Animation(obj, 'position', 1, 2, 0)``.
    """
    def __init__(self, num_dimensions, **kwargs):
        super(VectorProperty, self).__init__(*(0, ) * num_dimensions, **kwargs)

    def adjust_value(self, value):
        """Expand the given tuple to the correct number of dimensions
        """
        size = len(value)
        if size == self.size:
            return value
        elif size < self.size:
            return value + (0, ) * (self.size - size)
        else:
            raise ValueError('Too many dimensions for VectorProperty')
