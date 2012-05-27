"""Effect base & helper classes

The Effect is the base class that modify an AnimatedProperty.
:class:`~gillcup.Animation` is Effect's most important subclass.

Each Effect can be applied to one or more properties on one or more objects.
The value of these properties is then provided by the Effect's ``value``
property.
"""


class Effect(object):
    """Object that changes an AnimatedProperty

    Effects should have a `value` attribute that provides a value for the
    property.
    """
    is_constant = False

    def get_replacement(self):
        """Return an equivalent effect

        When it's sure that the effect's value won't change any more, this
        method can return a :class:`~gillcup.ConstantEffect` to free resources.
        """
        return self

    def apply_to(self, instance, property_name):
        """Apply this effect to an ``instance``'s AnimatedProperty"""
        getattr(type(instance), property_name).animate(instance, self)


class ConstantEffect(Effect):
    """An Effect that provides a constant value"""
    is_constant = True

    def __init__(self, value):
        super(ConstantEffect, self).__init__()
        self.value = value
