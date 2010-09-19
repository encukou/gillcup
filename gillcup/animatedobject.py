
class AnimatedObject(object):
    """An objects whose attributes can be animated

    Animated attribute must be instance (not class) attribute in order to
    work.
    Every animated attribute must be assigned a normal value before it can be
    animated. Usually this is done in the constructor.
    """
    def __init__(self):
        self._anim_data_ = {}

    def _animate(self, attribute, animation):
        try:
            old = self.__dict__[attribute]
            del self.__dict__[attribute]
        except KeyError:
            old = self._anim_data_[attribute].getValue
        else:
            old = lambda: oldValue
        self._anim_data_[attribute] = animation
        return old

    def __getattr__(self, attr):
        return self._anim_data_[attribute].getValue()
