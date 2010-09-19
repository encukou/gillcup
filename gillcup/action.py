

class Action(object):
    """Something that can be scheduled: a discrete event.

    Also, other Actions can be chained to it. These will be run
    when the "parent" Action, or when an effect applied by it, finishes.

    An Action object is scheduled for the future. It generally has no use
    once the event it represents happens.
    """
    def __init__(self):
        self.chain = []

    def chain(self, *others):
        self.chain.append(others)


def NullAction(Action):
    def run(self, timer):
        for ch in self.chain:
            ch.run(timer)


class FunctionAction(Action):
    def __init__(self, func, kwargs={}, passTimer=False, *args):
        Action.__init__(self)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.passTimer = passTimer

    def run(self, timer):
        if self.passTimer:
            kwargs = dict(timer=timer)
            kwargs.update(self.kwargs)
        else:
            kwargs = self.kwargs
        self.func(*self.args, **kwargs)
        for ch in self.chain:
            ch.run(timer)


class EffectAction(Action):
    def __init__(self, effect, *args, **kwargs):
        Action.__init__(self, func)
        self.effect = effect
        self.args = args
        self.kwargs = kwargs

    def run(self, timer):
        self.effect.start(timer, args, kwargs)
        self.effect.chain(*self.chain)
