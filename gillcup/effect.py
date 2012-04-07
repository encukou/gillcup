"""Effect base & helper classes

Moved to a separate module mainly to solve dependency/import order problems
"""


class Effect(object):
    """Object that changes an AnimatedProperty

    Effects should have a `value` attribute that provides a value for the
    property.
    """
    def get_replacement(self):
        """Return an equivalent effect

        When it's sure that the effect's value won't change any more, this
        method can return a ConstantEffect to free resources.
        """
        return self

    def apply_to(self, instance, property_name):
        """Apply this effect to an ``instance``'s AnimatedProperty"""
        getattr(type(instance), property_name).animate(instance, self)


class ConstantEffect(Effect):
    """An Effect that provides a constant value
    """
    def __init__(self, value):
        super(ConstantEffect, self).__init__()
        self.value = value
