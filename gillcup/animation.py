from __future__ import division

from gillcup.actions import Action
from gillcup.effect import Effect
from gillcup.properties import AnimatedProperty
from gillcup import easing as easing_module

class Animation(Effect, Action):
    """An Animation that modifies a scalar animated property

    Positional init arguments:

    :argument object:

        The object whose property is animated

    :argument property_name:

        Name of the animated property

    :argument target:

        Value at which the animation should arrive (tuple properties
        accept more arguments, i.e. ``Animation(obj, 'position', 1, 2, 3)``)

    Keyword init arguments:

    :argument time:

        The duration of the animation

    :argument delay:

        Delay between the time the animation is scheduled and its actual start

    :argument timing:

        A function that maps global time to animation's time.

        Possible values:

        *   ``None``: normalizes time so that 0 corresponds to the start of the
            animation, and 1 to the end (i.e. start + `time`); clamps to [0, 1]
        *   ``'infinite'``: same as above, but doesn't clamp: the animation
            goes forever on (in both directions; it only starts to take effect
            when it's scheduled, but a `delay` can cause negative local times).
            The animation's time is normalized to 0 at the start and
            1 at start + `time`.
        *   ``'absolute'``: the animation is infinite, with the same speed as
            with the 'infinite' option, but zero corresponds to the clock's
            zero.
            Useful for synchronized periodic animations.
        * `function(time, start, duration)`: apply a custom function

    :argument easing:

        An easing function to use. Can be either a one-argument
        function, or a dotted name which is looked up in the
        :mod:`gillcup.easing` module.

    :argument dynamic:

        If true, the **target** atribute becomes an AnimatedProperty, allowing
        for more complex animations.
    """

    def __init__(self, object, property_name, *target, **kwargs):
        super(Animation, self).__init__()
        self.object = object
        self.property = self.get_property(object, property_name)

        try:
            new_target = kwargs.pop('target')
        except KeyError:
            pass
        else:
            if target:
                raise ValueError('Target specified as both positional and ' +
                    'keyword arguments')
            target = new_target

        self.target = self.property.adjust_value(target)

        self.time = kwargs.pop('time', 1)
        self.delay = kwargs.pop('delay', 0)
        easing = kwargs.pop('easing', 'linear')
        timing = kwargs.pop('timing', None)

        if timing == 'infinite':
            self.get_time = self._infinite_timing
        elif timing == 'absolute':
            self.get_time = self._absolute_timing
        elif timing:
            self.get_time = lambda: timing(
                    self.clock.time, self.start_time, self.time)

        if isinstance(easing, basestring):
            e = easing_module
            for attr in easing.split('.'):
                e = getattr(e, attr)
            self.easing = e
        else:
            self.easing = easing

    @classmethod
    def get_property(self, object, property_name):
        return getattr(type(object), property_name)

    def __new__(cls, object, property_name, *args, **kwargs):
        if kwargs.pop('dynamic', False):
            # We need the target to act the same as the animated property
            # (wrt adjust_value: being scalar/tuple, etc).
            # An AnimatedProperty needs to be on a class, we can't just put
            # a descriptor on an instance.
            # So, we create a trivial subclass that has the target property.
            class AnimatedAnimation(cls):
                prop = cls.get_property(object, property_name)
                target = prop.get_target_property()
            ani_class = AnimatedAnimation
        else:
            ani_class = cls
        super_new = super(Animation, cls).__new__
        return super_new(ani_class, object, property_name, *args, **kwargs)

    def __call__(self):
        self.expire()
        self.parent = self.property.animate(self.object, self)
        self.start_time = self.clock.time + self.delay
        self.clock.schedule(self.trigger_chain, self.time + self.delay)

    @property
    def value(self):
        parent_value = self.parent.value
        target = self.target
        return self.property.map(self.compute_value, parent_value, target)

    def get_time(self):
        elapsed = self.clock.time - self.start_time
        if elapsed < 0:
            return 0
        if elapsed > self.time:
            return 1
        else:
            return elapsed / self.time
    get_time.finite = True

    def _absolute_timing(self):
        return self.clock.time / self.time

    def _infinite_timing(self):
        return (self.clock.time - self.start_time) / self.time

    def compute_value(self, previous, target):
        t = self.easing(self.get_time())
        return previous * (1 - t) + target * t

class Add(Animation):
    """An additive animation: the target value is added to the original
    """
    def compute_value(self, previous, target):
        t = self.easing(self.get_time())
        return previous + target * t

class Multiply(Animation):
    """A multiplicative animation: target value is multiplied to the original
    """
    def compute_value(self, previous, target):
        t = self.easing(self.get_time())
        return previous * ((1 - t) + target * t)

class Computed(Animation):
    """A custom-valued animation: the target is computed by a function

    Pass a **func** keyword argument with the function to the constructor.

    The function will get one argument: the time elapsed, normalized by the
    animation's `timing` function.
    """
    def __init__(self, object, property_name, **kwargs):
        self.func = kwargs.pop('func')
        prop = self.get_property(object, property_name)
        kwargs.setdefault('target', [prop.default])
        super(Computed, self).__init__(object, property_name, **kwargs)

    def compute_value(self, previous, target):
        t = self.get_time()
        return self.func(t)
