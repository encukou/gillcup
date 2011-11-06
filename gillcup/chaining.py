# Encoding: UTF-8

def noop():
    return

class Chainable(object):
    """Base class for the chaining functionality of Action

    Actions (or callables) can be “chained” to a Chainable.
    When the Chainable is “triggered”, via `trigger_chain()`, all chained
    actions are scheduled on the given Clock.
    """
    def __init__(self):
        # A list of (dt, action) tuples for chained actions
        self._chain = []

    def chain(self, action, dt=0):
        """Schedule an action to be scheduled after this Chainable

        The dt argument can be given to delay the chained action by the
        specified time.

        Returns the chained action.
        """
        self._chain.append((action, dt))
        return action

    def trigger_chain(self, clock):
        """Schedule the chained actions.
        """
        for dt, chained in self._chain:
            clock.schedule(dt, chained)

class _Aggregate(Chainable):
    """Base class for WaitForAll and WaitForAny"""
    def __init__(self, clock=None):
        super(_Aggregate, self).__init__()
        self._actions = set()
        if clock:
            self._clock = clock

    @property
    def clock(self):
        try:
            return self._clock
        except AttributeError:
            clocks = set(a.clock for a in self._actions)
            try:
                (clock, ) = clocks
                return clock
            except ValueError:
                if clocks:
                    raise ValueError(
                        "Waited-for actions don't all share the same clock")
                else:
                    raise ValueError(
                        "No waited-for action has a clock")

class WaitForAll(_Aggregate):
    """A Chainable that triggers after all given actions are triggered

    If `clock` is not given as a keyword argument to __init__, all waited-for
    actions must have a `clock`, which is used to shedule chained actions on.
    """
    def __init__(self, *actions, **kwargs):
        super(WaitForAll, self).__init__(kwargs.get('clock'))
        if actions:
            self.add(*actions)

    def add(self, *actions):
        """Add an action to the set of actions waited for
        """
        for action in actions:
            self._actions.add(action)
            def trigger_action(action=action):
                self._trigger(action)
            action.chain(trigger_action)

    def _trigger(self, action):
        clock = self.clock
        self._actions.remove(action)
        if not self._actions:
            self.trigger_chain(clock)

class WaitForAny(_Aggregate):
    """A Chainable that triggers after any of the given actions are triggered.

    If `clock` is not given as a keyword argument to __init__, all waited-for
    actions must have a `clock`, which is used to shedule chained actions on.
    """
    def __init__(self, *actions, **kwargs):
        super(WaitForAny, self).__init__(kwargs.get('clock'))
        if actions:
            self.add(*actions)
        self.has_triggered = False

    def add(self, *actions):
        """Add an action to the set of actions waited for
        """
        for action in actions:
            self._actions.add(action)
            action.chain(self._trigger)

    def _trigger(self):
        if not self.has_triggered:
            self.has_triggered = True
            self.trigger_chain(self.clock)
