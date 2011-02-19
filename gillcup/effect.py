
from __future__ import division

from gillcup.animatedobject import AnimatedObject
from gillcup.action import Action, FunctionAction, EffectAction


class Effect(AnimatedObject):
    """Dynamically changes an AnimatedObject's attribute over time

    The most important method is getValue, which determines what the associated
    attribute will be.

    An effect usually has an "end" action.
    Chaining an action to an effect chains it to the effect's end.
    """
    def __init__(self, end=None):
        super(Effect,self).__init__()
        if end is None:
            self._end = Action()
        else:
            self._end = end

    def chain(self, *actions, **kwargs):
        return self._end.chain(*actions, **kwargs)

    def start(self, timer, object, attribute):
        self.timer = timer
        self.startTime = self.timer.time
        self.object = object
        self.attribute = attribute
        self.old = object._animate(attribute, self)


    def replace(self, newEffect):
        return self.object._replace_effect(self.attribute, self, newEffect)

    def _replace_effect_(self, oldEffect, newEffect):
        try:
            currentEffect = self.old
        except KeyError:
            return False
        else:
            if currentEffect is oldEffect:
                self.old = newEffect
            else:
                currentEffect._replace_effect_(oldEffect, newEffect)


class GetterObject(object):
    def __init__(self, getValue, isConstant=False):
        self.getValue = getValue
        self._is_constant = isConstant

    def dump(self, indentationLevel):
        if self._is_constant:
            print '  ' * indentationLevel, 'GetterObject (constant)'
        else:
            print '  ' * indentationLevel, 'GetterObject (expression)'

    def _replace_effect_(self, oldEffect, newEffect):
        return

class InterpolationEffect(Effect):
    """The most useful effect. Interpolates a value.

    This object is designed so that most of its methods can be overriden
    at the instance level.
    """
    finalized = False

    def __init__(self, value, time, *args, **kwargs):
        Effect.__init__(self, *args, **kwargs)
        self.value = value
        self.time = time
        self.strength = 1

    def start(self, *args, **kwargs):
        Effect.start(self, *args, **kwargs)
        self.timer.schedule(self.time, self._end)

    def finalize(self):
        """End the effect

        After calling this method, the Effect will always return the value
        at t=1, and most attempts to change it will fail.
        """
        finalValue = self.getValue()
        self.getValue = lambda: finalValue
        self.replace(GetterObject(self.getValue, isConstant=True))
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

    def oldValue(self):
        return self.old.getValue()

    def getValue(self):
        t = self.getTime()
        t = self.clampTime(t)
        t = self.ease(t)
        t *= self.strength
        return self.interpolate(self.oldValue(), self.value, t)

    def dump(self, indentationLevel):
        name = type(self).__name__
        try:
            name = '"' + self.name + '" ' + name
        except AttributeError:
            pass
        print '  ' * indentationLevel + name
        indentationLevel += 1
        if self.strength != 1:
            print '  ' * indentationLevel + 'x' + str(self.strength)
        time = self.getTime()
        if time:
            print '  ' * indentationLevel + '@' + str(time)
            clamped = self.clampTime(time)
            if time != clamped:
                print '  ' * indentationLevel + '  [>]' + str(clamped)
        print '  ' * indentationLevel + '>' + str(self.value)
        AnimatedObject._dump_effects(self, indentationLevel)
        print '  ' * indentationLevel + 'base:' + str(self.old.getValue())
        try:
            dump = self.old.dump
        except AttributeError:
            print '  ' * (indentationLevel + 1) + str(self.old)
        else:
            self.old.dump(indentationLevel + 1)

def animation(object, attribute, value, *morevalues, **kwargs):
    """Convenience function to create various Interpolation effects on
    objects.

    [XXX] Document once the API settles a bit
    """
    if morevalues:
        value = (value, ) + morevalues
    time = kwargs.pop('time', 0)
    infinite = kwargs.pop('infinite', False)
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
    cls = kwargs.pop('cls', None)
    if not cls:
        cls = InterpolationEffect
    else:
        keep = True
    effect = cls(value, time)
    if time == 'absolute':
        effect.time = time = 1
        effect.getTime = lambda: effect.timer.time
        infinite = True
    if time == 'dynamic':
        effect.time = time = 0
        infinite = True
    easing = kwargs.pop('easing', None)
    if easing:
        if isinstance(easing, basestring):
            attrarray = easing.split()
            from gillcup import easing
            for a in attrarray:
                easing = getattr(easing, a)
        effect.ease = easing
    if infinite:
        effect.clampTime = lambda t: t
    elif not keep:
        if not time:
            value = interpolate(getattr(object, attribute), value, 1)
            return FunctionAction(setattr, object, attribute, value)
        else:
            effect.chain(FunctionAction(effect.finalize))
    if not time:
        effect.getTime = lambda: 1
    oldValue = kwargs.pop('start', None)
    if oldValue is not None:
        effect.oldValue = lambda: oldValue
    effect.interpolate = interpolate
    name = kwargs.pop('name', None)
    if name:
        effect.name = name
    effect.timer = object.timer
    return EffectAction(effect, object, attribute)
