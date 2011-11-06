from __future__ import division

from gillcup.actions import Action
from gillcup.effect import Effect

class Animation(Effect, Action):
    """An Animation: Action that modifies an animated property
    """

    def __init__(self, object, property_name, target, time=1):
        super(Animation, self).__init__()
        self.object = object
        self.target = target
        self.time = time
        self.parent = None

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
        self.start_time = self.clock.time
        self.clock.schedule(self.trigger_chain, self.time)

    @property
    def value(self):
        parent_value = self.parent.value
        target = self.target
        return self.property.map(self.compute_value, parent_value, target)

    def get_time(self):
        elapsed = self.clock.time - self.start_time
        if elapsed > self.time:
            return 1
        else:
            return (self.clock.time - self.start_time) / self.time

    def compute_value(self, previous, target):
        t = self.get_time()
        return previous * (1 - t) + target * t

class Add(Animation):
    """An additive animation: the target value is added to the original
    """
    def compute_value(self, previous, target):
        t = self.get_time()
        return previous + target * t

class Multiply(Animation):
    """A multiplicative animation: the target value is multiplied to the original
    """
    def compute_value(self, previous, target):
        t = self.get_time()
        return previous * ((1 - t) + target * t)

class Computed(Animation):
    """A custom-valued animation: the target is computed by a function

    Pass a `func` keyword argument with the function to the constructor.

    The function will getone argument, the time elapsed, normalized so that
    0 corresponds to the start of the animation, and 1 to the
    end (i.e. start + `time`).
    """
    def __init__(self, *args, **kwargs):
        self.func = kwargs.pop('func')
        kwargs.setdefault('target', self.property.default)
        super(Computed, self).__init__(*args, **kwargs)

    def compute_value(self, previous, target):
        t = self.get_time()
        return self.func(t)
