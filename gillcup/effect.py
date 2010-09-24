
from __future__ import division

from gillcup.action import Action, FunctionAction, EffectAction


class Effect(object):
    """Something that exists over a longer time: a continuous animation

    An effect usually has an "end" action.
    Chaining an action to an effect chains it to the effect's end.
    """
    def __init__(self, end=None):
        if end is None:
            self._end = Action()
        else:
            self._end = end

    def chain(self, *actions, **kwargs):
        return self._end.chain(*actions, **kwargs)


class AttributeEffect(Effect):
    """An Effect that dynamically changes an AnimatedObject's attribute
    """
    def start(self, timer, object, attribute):
        self.timer = timer
        self.startTime = self.timer.time
        self.object = object
        self.attribute = attribute
        self.old = object._animate(attribute, self)


    def replace(self, newEffect):
        return self.object._replace_effect(self.attribute, self, newEffect)

    def _replace_effect(self, oldEffect, newEffect):
        try:
            currentEffect = self.old
        except KeyError:
            return False
        else:
            if currentEffect is oldEffect:
                self.old = newEffect
            else:
                currentEffect._replace_effect(oldEffect, newEffect)


class GetterObject(object):
    def __init__(self, getValue):
        self.getValue = getValue


class InterpolationEffect(AttributeEffect):
    """The most useful effect. Interpolates a value.

    This object is designed so that most of its methods can be overriden
    at the instance level.
    """
    finalized = False

    def __init__(self, value, time, *args, **kwargs):
        AttributeEffect.__init__(self, *args, **kwargs)
        self.value = value
        self.time = time

    def start(self, *args, **kwargs):
        AttributeEffect.start(self, *args, **kwargs)
        self.timer.schedule(self.time, self._end)

    def finalize(self):
        """End the effect

        After calling this method, the Effect will always return the value
        at t=1, and most attempts to change it will fail.
        """
        finalValue = self.getValue()
        self.getValue = lambda: finalValue
        self.replace(GetterObject(self.getValue))
        self.old = self.time = self.timer = self.clampTime = self.ease = None
        self.finalized = True

    @staticmethod
    def interpolateScalar(a, b, t):
        return a * (1 - t) + b * t

    interpolate = interpolateScalar

    def getTime(self):
        return (self.timer.time - self.startTime) / self.time

    @staticmethod
    def ease(t):
        return t

    @staticmethod
    def clampTime(t):
        if t <= 0:
            return 0
        elif t >= 1:
            return 1
        else:
            return t

    def getValue(self):
        t = self.getTime()
        t = self.clampTime(t)
        t = self.ease(t)
        return self.interpolate(self.old.getValue(), self.value, t)

def animation(object, attribute, value, *morevalues, **kwargs):
    """Convenience function to create various Interpolation effects on
    objects.
    """
    if morevalues:
        value = (value, ) + morevalues
    time = kwargs.pop('time', 0)
    if kwargs.pop('additive', False):
        interpolateScalar = lambda a, b, t: a + b * t
        keep = kwargs.pop('keep', True)
    elif kwargs.pop('multiplicative', False):
        interpolateScalar = lambda a, b, t: a * ((t - 1) + b * t)
        keep = kwargs.pop('keep', True)
    else:
        interpolateScalar = InterpolationEffect.interpolateScalar
        keep = kwargs.pop('keep', False)
    if isinstance(value, tuple):
        interpolate = lambda a, b, t: tuple(
                interpolateScalar(aa, bb, t) for aa, bb in zip(a, b)
            )
    else:
        interpolate = interpolateScalar
    effect = InterpolationEffect(value, time)
    easing = kwargs.pop('easing', None)
    if easing:
        if isinstance(easing, basestring):
            attrarray = easing.split()
            from gillcup import easing
            for a in attrarray:
                easing = getattr(easing, a)
        effect.ease = easing
    if kwargs.pop('infinite', False):
        effect.clampTime = lambda t: t
    elif not keep:
        effect.chain(FunctionAction(effect.finalize))
    elif not time:
        value = interpolate(getattr(object, attribute), value, 1)
        return FunctionAction(setattr, object, attribute, value)
    if not time:
        effect.getTime = lambda: 1
    effect.interpolate = interpolate
    return EffectAction(effect, object, attribute)


