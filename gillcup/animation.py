# Encoding: UTF-8
"""Gillcup's Animation classes

Animations are :mod:`Actions <gillcup.actions>` that modify
:mod:`animated properties <gillcup.properties>`.
To use one, create it and schedule it on a Clock.
Once an animation is in effect, it will smoothly change a property's value
over a specified time interval.

The value is computed as a tween between the property's original value and
the Animation's **target** value.
The tween parameters can be set by the **timing** and **easing** keyword
arguments.

The “original value” of a property is not fixed: it is whatever the
value would have been if this animation wasn't applied.
Also, if you set the **dynamic** argument to Animation, the animation's
*target* becomes an :class:`~gillcup.AnimatedProperty`.
Animating these allows one to create very complex effects in a modular way.
"""

from __future__ import unicode_literals, division, print_function

from six import string_types

from gillcup.actions import Action
from gillcup.effect import Effect, ConstantEffect
from gillcup import easing as easing_module


class Animation(Effect, Action):
    """An Animation that modifies a scalar animated property

    Positional init arguments:

    :argument instance:

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

    .. note::

        In order to conserve resources, ordinary Animations are released when
        they are “done”. This is done by effectively replacing them with
        an animation whose value is constant.
        When using arguments such as ``timing`` and ``dynamic``, or the
        :class:`~gillcup.animation.Add` or :class:`~gillcup.animation.Multiply`
        animations, which allow the value to be modified after the ``time``
        elapses, turns this behavior off by setting the ``dynamic`` attibute
        to true.

        When subclassing Animation, remember to do the same if your subclass
        needs to change its value after ``time`` elapses.
        This includes cases where the value depends on the value of the
        previous (parent) animation.
    """
    dynamic = False

    start_time = None
    parent = None

    def __init__(self, instance, property_name, *target, **kwargs):
        super(Animation, self).__init__()
        self.instance = instance
        self.property = self.get_property(instance, property_name)

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

        self.dynamic = (self.dynamic or 'timing' in kwargs or
            kwargs.pop('dynamic', False))
        if not self.dynamic:
            self.chain(lambda: self.property.do_replacements(instance))

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

        if isinstance(easing, string_types):
            e = easing_module
            for attr in easing.split('.'):
                e = getattr(e, attr)
            self.easing = e
        else:
            self.easing = easing

    @classmethod
    def get_property(cls, instance, property_name):
        """Get a property object off an instance's class"""
        return getattr(type(instance), property_name)

    def __new__(cls, instance, property_name, *args, **kwargs):
        if kwargs.get('dynamic', False):
            # We need the target to act the same as the animated property
            # (wrt adjust_value: being scalar/tuple, etc).
            # An AnimatedProperty needs to be on a class, we can't just put
            # a descriptor on an instance.
            # So, we create a trivial subclass that has the target property.
            prop = cls.get_property(instance, property_name)

            class AnimatedAnimation(cls):
                """A more dynamic flavor of gillcup.Animation"""
                target = prop.get_target_property()
            ani_class = AnimatedAnimation
        else:
            ani_class = cls
        super_new = super(Animation, cls).__new__
        return super_new(ani_class, instance, property_name, *args, **kwargs)

    def __call__(self):
        self.expire()
        self.parent = self.property.animate(self.instance, self)
        self.start_time = self.clock.time + self.delay
        self.clock.schedule(self.trigger_chain, self.time + self.delay)

    @property
    def value(self):
        """Value to be used for the property this animation is on"""
        parent_value = self.parent.value
        target = self.target
        return self.property.tween_values(self.compute_value,
                parent_value, target)

    def get_time(self):  # pylint: disable=E0202
        """Get the local time for tweening, usually in the [0..1] range"""
        elapsed = self.clock.time - self.start_time
        if elapsed <= 0:
            return 0
        if elapsed >= self.time:
            return 1
        else:
            return elapsed / self.time
    get_time.finite = True

    def _absolute_timing(self):
        return self.clock.time / self.time

    def _infinite_timing(self):
        return (self.clock.time - self.start_time) / self.time

    def compute_value(self, previous, target):
        """Given the previous value and a target, compute value"""
        t = self.easing(self.get_time())
        return previous * (1 - t) + target * t

    def get_replacement(self):
        self.parent = self.parent.get_replacement()
        if not self.dynamic and self.get_time() >= 1:
            # Not gonna change from now on
            return ConstantEffect(self.value)
        else:
            return self


class Add(Animation):
    """An additive animation: the target value is added to the original
    """
    dynamic = True

    def compute_value(self, previous, target):
        t = self.easing(self.get_time())
        return previous + target * t


class Multiply(Animation):
    """A multiplicative animation: target value is multiplied to the original
    """
    dynamic = True

    def compute_value(self, previous, target):
        t = self.easing(self.get_time())
        return previous * ((1 - t) + target * t)


class Computed(Animation):
    """A custom-valued animation: the target is computed by a function

    Pass a **func** keyword argument with the function to the constructor.

    The function will get one argument: the time elapsed, normalized by the
    animation's `timing` function.
    """
    def __init__(self, instance, property_name, func, **kwargs):
        self.func = func
        prop = self.get_property(instance, property_name)
        kwargs.setdefault('target', [prop.default])
        super(Computed, self).__init__(instance, property_name, **kwargs)

    def compute_value(self, previous, target):
        t = self.get_time()
        return self.func(t)
