

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
        self.expired = False

    def chain(self, action, *others, **kwargs):
        """Schedule an Action (or more) at the end of this Action

        The dt argument can be given to delay the runnin of the execution
        by the specified time.

        For EffectAction, the actions are scheduled after the applied effect
        ends.

        If this action has already finished, the chained ones are scheduled
        immediately.
        """
        if self.expired:
            self.timer.schedule(kwargs.get('dt', 0), action, *others)
        else:
            for act in (action,) + others:
                self._chain.append((kwargs.get('dt', 0), act))
        return action

    def run(self, timer):
        """Run this action.

        Called from a Timer.
        """
        if self.expired:
            raise RuntimeError('An Action is being run twice')
        self.expired = True
        self.timer = timer
        for dt, ch in self._chain:
            timer.schedule(dt, ch)

    def delay(self, dt):
        """Schedule a null action at time dt (useful in chaining)
        """
        return self.chain(Action(), dt=dt)

class FunctionAction(Action):
    """An Action that executes a function when run

        func is called when this Action is run; args are passed to it

        Additional options:

        - kwargs: a dict of named arguments to pass to the function
        - passTimer: if True, the timer will be passed as an additional named
          argument
    """
    def __init__(self, func, *args, **options):
        Action.__init__(self)
        self.func = func
        self.args = args
        self.kwargs = options.get('kwargs', {})
        self.passTimer = options.get('passTimer', False)

    def run(self, timer):
        Action.run(self, timer)
        if self.passTimer:
            kwargs = dict(timer=timer)
            kwargs.update(self.kwargs)
        else:
            kwargs = self.kwargs
        self.func(*self.args, **kwargs)


class EffectAction(Action):
    """An Action that applies an effect when run

        effect is applied when this Action is run; the timer, args and kwargs
        are passed to it.

        args should be the object and attribute to apply the Effect to.
    """

    def __init__(self, effect, *args, **kwargs):
        Action.__init__(self)
        self.effect = effect
        self.args = args
        self.kwargs = kwargs

    def run(self, timer):
        self._chain, chain = [], self._chain
        Action.run(self, timer)
        self.effect.start(timer, *self.args, **self.kwargs)
        for dt, ch in chain:
            self.effect.chain(ch, dt=dt)


class WaitForAll(Action):
    """An Action that waits for other actions, and runs when they all are run
    """
    def __init__(self, *actions):
        Action.__init__(self)
        self.pending_actions = set(actions)
        for action in self.pending_actions:
            action.chain(FunctionAction(self.triggered, action))

    def triggered(self, action):
        self.pending_actions.remove(action)
        if not self.pending_actions:
            self.run(action.timer)


class WaitForAny(Action):
    """An Action that waits for other actions, and runs when any of them is run
    """
    def __init__(self, *actions):
        Action.__init__(self)
        for action in actions:
            action.chain(self.maybeRun)

    def maybeRun(self, timer):
        if not self.expired:
            self.run()
