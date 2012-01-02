
from gillcup.effect import Effect, ConstantEffect

try:
    from functools import lru_cache
except ImportError:
    lru_cache = lambda n=100: lambda func: func

class AnimatedProperty(object):
    """A scalar animated property
    """
    def __init__(self, default, docstring=None):
        self.default = default
        if docstring:
            self.__doc__ = docstring

    @lru_cache()
    def animation_class_factory(self, superclass):
        class CustomAnimation(superclass):
            target = self
        return CustomAnimation

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

        Reimplemented in TupleProperty
        """
        return function(parent_value, value)

class TupleProperty(AnimatedProperty):
    """A tuple animated property

    Iterating this yields sub-properties that can be animated individually.
    The intended idiom for declaring a tuple property is:

        x, y, z = position = TupleProperty(3, (0, 0, 0))
    """
    def __init__(self, size, default):
        if len(default) != size:
            raise ValueError('Default is not of the correct size')
        super(TupleProperty, self).__init__(default)
        self.size = size
        self.subproperties = [_TupleElementProperty(self, i)
                for i in xrange(self.size)]

    @lru_cache()
    def animation_class_factory(self, superclass):
        super_factory = super(TupleProperty, self).animation_class_factory
        anim_class = super_factory(superclass)
        def init(self, object, property_name, *target, **kwargs):
            super(anim_class, self).__init__(object,
                    property_name, target, **kwargs)
        anim_class.__init__ = init
        return anim_class

    def __iter__(self):
        return iter(self.subproperties)

    def map(self, function, parent_value, value):
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
