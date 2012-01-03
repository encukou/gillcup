# Encoding: UTF-8

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
            return self._get_effect(instance).value
        else:
            return self

    def __set__(self, instance, value):
        self.animate(instance, ConstantEffect(value))

    def _get_effect(self, instance):
        try:
            _gillcup_effects = instance._gillcup_effects
        except AttributeError:
            _gillcup_effects = instance._gillcup_effects = {}
        try:
            effect = _gillcup_effects[self]
        except KeyError:
            effect = _gillcup_effects[self] = ConstantEffect(self.default)
        return effect

    def animate(self, instance, animation):
        parent = self._get_effect(instance)
        instance._gillcup_effects[self] = animation
        return parent

    def map(self, function, parent_value, value):
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
                for i in xrange(self.size)]

    def adjust_value(self, value):
        """Convert an animation's ``*args`` values into a property value

        For tuple properties, return the tuple unchanged
        """
        return value

    def __iter__(self):
        return iter(self.subproperties)

    def map(self, function, parent_value, value):
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

    def _get_effect(self, instance):
        parent_effect = self.parent._get_effect(instance)
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
        self.parent = parent
        self.index = index

    @property
    def value(self):
        return self.parent.value[self.index]

class _TupleMakeEffect(Effect):
    """Effect that recombines one changed element of a tuple with the rest

    `parent` is an Effect whose `value` is used for the changed element

    The `previous` attribute has the Effect with the original, full tuple.
    This attribute must be set after instantiation.
    """
    def __init__(self, parent, index):
        self.parent = parent
        self.index = index

    @property
    def value(self):
        parent = self.parent
        return tuple(parent.value if i == self.index else val
            for i, val in enumerate(self.previous.value))
        return self.parent.value[self.index]
