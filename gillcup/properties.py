
from gillcup.animation import Effect, ConstantEffect

class AnimatedProperty(object):
    """An animated property
    """
    def __init__(self, default):
        self.default = default

    def __get__(self, instance, owner):
        if instance:
            return self._get_effect(instance).value
        else:
            return self

    def __set__(self, instance, value):
        if isinstance(value, Effect):
            self.animate(instance, value)
        else:
            try:
                instance._gillcup_effects[self] = ConstantEffect(value)
            except AttributeError:
                instance._gillcup_effects = {}
                instance._gillcup_effects[self] = ConstantEffect(value)

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
