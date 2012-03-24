
"""Effect

Moved to a separate module to solve dependency/import order problems
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

class ConstantEffect(Effect):
    """An Effect that provides a constant value
    """
    def __init__(self, value):
        self.value = value
