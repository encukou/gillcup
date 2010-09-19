
from gillcup.action import NullAction


class Effect(object):
    """Something that exists over a longer time: a continuous animation

    An effect usually has an "end" action.
    Chaining an action to an effect chains it to the effect's end.
    """
    def __init__(self, end=None):
        if end is None:
            self.end = NullAction()
        else:
            self.end = end

    def chain(self, *actions):
        self.end.chain(*actions)


class AttributeEffect(Effect):
    """An Effect that dynamically changes an AnimatedObject's attribute
    """
    def start(self, timer, object, attribute):
        self.timer = timer
        self.startTime = self.timer.time
        self.object = object
        self.attribute = attribute
        self.old = object._animate(attribute, self)


class Interpolate(AttributeEffect):
    """The most useful effect. Interpolates a value.
    """
    def __init__(self, value, time, *args, **kwargs):
        PropertyEffect.__init__(self, *args, **kwargs)
        self.value = value
        self.time = time
        self.ended = False

    def start(self, *args, **kwargs):
        PropertyEffect.start(self, *args, **kwargs)
        self.timer.schedule(self.time, self.end)

    def interpolateValue(self, a, b, t):
        if isinstance(b, tuple):
            return tuple(
                    self.interpolateValue(aa, bb, t)
                    for aa, bb in zip(a, b))
        else:
            return a * (1 - t) + b * t

    def getTime(self):
        return self.timer

    def ease(self, t):
        return t

    def clampTime(self, t):
        if t <= 0:
            return 0
        elif t >= 1:
            return 1
        else:
            return t

    def getValue(self):
        t = self.ease(self.clampTime(self.getTime()))
        return self.interpolateValue(self.old(), self.value, t)
