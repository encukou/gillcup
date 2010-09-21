

class Action(object):
    """Something that can be scheduled: a discrete event.

    Also, other Actions can be chained to it.
    These will be run when the "parent" Action, or an effect applied by it,
    finishes.

    Actions may not be callable. If they are, they won't be scheduled as
    actions.
    """
    def __init__(self):
        self._chain = []

    def chain(self, *others, **kwargs):
        for other in others:
            self._chain.append((kwargs.get('dt', 0), other))

    def run(self, timer):
        for dt, ch in self._chain:
            timer.schedule(dt, ch)


class FunctionAction(Action):
    def __init__(self, func, *args, **options):
        Action.__init__(self)
        self.func = func
        self.args = args
        self.kwargs = options.get('kwargs', {})
        self.passTimer = options.get('passTimer', False)

    def run(self, timer):
        if self.passTimer:
            kwargs = dict(timer=timer)
            kwargs.update(self.kwargs)
        else:
            kwargs = self.kwargs
        self.func(*self.args, **kwargs)
        for dt, ch in self._chain:
            timer.schedule(dt, ch)


class EffectAction(Action):
    def __init__(self, effect, *args, **kwargs):
        Action.__init__(self)
        self.effect = effect
        self.args = args
        self.kwargs = kwargs

    def run(self, timer):
        self.effect.start(timer, *self.args, **self.kwargs)
        for dt, ch in self._chain:
            self.effect.chain(dt, ch)
