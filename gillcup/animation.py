from __future__ import division

from gillcup.actions import Action
from gillcup.effect import Effect
from gillcup import easing as easing_module

class Animation(Effect, Action):
    """An Animation: Action that modifies an animated property

    Init arguments:
    - `object`: The object whose property is animated
    - `property_name`: Name of the animated property
    - `target`: Value at which the animation should arrive (tuple properties
        accept more arguments, i.e. `Animation(obj, 'position', 1, 2, 3)`)
    - `time`: The duration of the animation
    - `delay`: Delay between the time the animation is scheduled and its start
    - `timing`: A function that maps global time to animation's time.
        Possible values:
        - None: normalizes time so that 0 corresponds to the start of the
            animation, and 1 to the end (i.e. start + `time`); clamps to [0, 1]
        - 'infinite': same as above, but doesn't clamp: the animation goes
            forever on (in both directions; it only starts to take effect when
            it's scheduled, but a `delay` can cause negative local times).
            The animation's time is normalized to 0 at the start and
            1 at start + `time`.
        - 'absolute': the animation is infinite, with the same speed as with
            the 'infinite' option, but zero corresponds to the clock's zero.
            Useful for synchronized periodic animations.
        - function(time, start, duration): apply a custom function
    - `easing`: An easing function to use. Can be either a one-argument
        function, or a dotted name which is looked up in the `gillcup.easing`
        module.
    """

    def __init__(self, object, property_name, target, time=1, delay=0,
            easing='linear', timing=None):
        super(Animation, self).__init__()
        self.object = object
        self.target = target
        self.time = time
        self.parent = None
        self.delay = delay

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

    def __new__(cls, object, property_name, *args, **kwargs):
        # Since descriptors can only be on classes, and we want `target` to
        # match whatever we're animating, we use a special subclass with
        # `target` set.
        # Also, tuple properties can be animated with *args.
        property = getattr(type(object), property_name)
        try:
            animation_class_factory = property.animation_class_factory
        except AttributeError:
            raise ValueError('%s is not an animated property' % property_name)
        super_new = super(Animation, cls).__new__
        anim_class = animation_class_factory(cls)
        instance = super_new(anim_class, object, property_name, *args, **kwargs)
        instance.property = getattr(type(object), property_name)
        return instance

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
        print self.clock.time, self.time
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
    """A multiplicative animation: the target value is multiplied to the original
    """
    def compute_value(self, previous, target):
        t = self.easing(self.get_time())
        return previous * ((1 - t) + target * t)

class Computed(Animation):
    """A custom-valued animation: the target is computed by a function

    Pass a `func` keyword argument with the function to the constructor.

    The function will getone argument, the time elapsed, normalized by the
    animation's `timing` function.
    """
    def __init__(self, *args, **kwargs):
        self.func = kwargs.pop('func')
        kwargs.setdefault('target', self.property.default)
        super(Computed, self).__init__(*args, **kwargs)

    def compute_value(self, previous, target):
        t = self.get_time()
        return self.func(t)
