
"""Effect

Moved to a separate module to solve dependency/import order problems
"""

class Effect(object):
    """Object that changes an AnimatedProperty

    Effects should have a `value` attribute that provides a value for the
    property.
    """
    pass

class ConstantEffect(Effect):
    """An Effect that provides a constant value
    """
    def __init__(self, value):
        self.value = value
