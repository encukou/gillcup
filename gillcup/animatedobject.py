
from gillcup.effect import animation

class AnimatedObject(object):
    """An objects whose attributes can be animated

    Animated attribute must be instance (not class) attribute in order to
    work.
    Every animated attribute must be assigned a normal value before it can be
    animated. Usually this is done in the constructor.

    Each AnimatedObject needs a timer to animate. This can be either
    through an argument to the animate method, or in an instance attribute.
    The constructor takes a timer value to set the instance attribute to.
    """
    def __init__(self, timer=None):
        super(AnimatedObject, self).__init__()
        self._anim_data_ = {}
        self.timer = timer

    def _animate(self, attribute, animation):
        try:
            oldValue = self.__dict__[attribute]
            del self.__dict__[attribute]
        except KeyError:
            old = self._anim_data_[attribute]
        else:
            class Old(object):
                def getValue(self):
                    return oldValue
            old = Old()
        self._anim_data_[attribute] = animation
        return old

    def __getattr__(self, attr):
        try:
            effect = self._anim_data_[attr]
        except KeyError:
            raise AttributeError(attr)
        except RuntimeError:
            # Probably _anim_data_ doesn't exist => infinite recursion
            raise RuntimeError(
                    'Runtime error while getting attribute %s. '
                    'Likely the base __init__ method was not called'
                    % attr
                )
        return effect.getValue()

    def _replace_effect(self, attribute, oldEffect, newEffect):
        try:
            currentEffect = self._anim_data_[attribute]
        except KeyError:
            return False
        else:
            if currentEffect is oldEffect:
                self._anim_data_[attribute] = newEffect
                return True
            else:
                return currentEffect._replace_effect(oldEffect, newEffect)

    def animate(self, attr, value, dt=0, timer=None, **options):
        anim = self.animation(attr, value, **options)
        return self.apply(anim, dt=dt, timer=timer)

    def animation(self, attr, value, **options):
        return animation(self, attr, value, **options)

    def apply(self, anim, dt=0, timer=None):
        timer = timer or self.timer
        timer.schedule(dt, anim)
        return anim
