
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
            old = self._anim_data_[attribute].getValue
        else:
            old = lambda: oldValue
        self._anim_data_[attribute] = animation
        return old

    def __getattr__(self, attr):
        try:
            return self._anim_data_[attr].getValue()
        except KeyError:
            raise AttributeError(attr)

    def animate(self, attr, value, dt=0, timer=None, **options):
        timer = timer or self.timer
        timer.schedule(dt, self.animation(attr, value, **options))

    def animation(self, attr, value, **options):
        return animation(self, attr, value, **options)
