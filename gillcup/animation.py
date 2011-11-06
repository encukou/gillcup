from __future__ import division

from gillcup.actions import Action

class Effect(object):
    pass

class ConstantEffect(Effect):
    def __init__(self, value):
        self.value = value

class Animation(Effect, Action):
    def __init__(self, object, property, target, time=1):
        super(Animation, self).__init__()
        self.object = object
        self.property = getattr(type(object), property)
        self.target = target
        self.time = time
        self.parent = None

    def __call__(self):
        self.expire()
        self.parent = self.property.animate(self.object, self)
        self.start_time = self.clock.time
        self.clock.schedule(self.trigger_chain, self.time)

    @property
    def value(self):
        return self.compute_value(self.parent.value, self.target)

    def get_time(self):
        elapsed = self.clock.time - self.start_time
        if elapsed > self.time:
            return 1
        else:
            return (self.clock.time - self.start_time) / self.time

    def compute_value(self, previous, target):
        t = self.get_time()
        return previous * (1 - t) + target * t
