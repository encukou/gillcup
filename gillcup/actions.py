# Encoding: UTF-8

import numbers

class Action(object):
    """An “event”.

    As any callable, an Action can be scheduled on a clock, either by
    clock.schedule(), or directly in the constructor.

    Other actions (the lowercase term denotes “arbitrary callables”) may be
    chained to an Action, that is, scheduled to run at some time after the
    Action is run.

    Some Actions may represent a time interval or process rather than a
    discrete point in time; in these cases, chained actions are run after the
    interval is over or the process finishes.

    Each Action may only be scheduled once. Initializing the class with the
    `clock` and `dt` arguments counts as scheduling.

    Actions may be combined to form larger structures with help of the Delay,
    Sequence and Parallel actions. As a shorthand, the following operators are
    available:
    - `+`: Creates a Sequence of actions; one is run after the other.
    - `|`: Creates a Parallel construct: all actions are started at once

    The operators can be usd with regular callables (which are wrapped in
    Actions), and with numbers (which create corresponding delays).
    """
    def __init__(self, clock=None, dt=0):
        super(Action, self).__init__()

        # Set to True once the Action runs
        self.expired = False

        # The chained actions
        self._chain = []

        # The clock
        self.clock = None
        if clock:
            clock.schedule(self, dt)
        else:
            if dt != 0:
                # We're not scheduling yet, so dt would be ignored
                raise ValueError('dt specified without a clock')

    def chain(self, action, dt=0):
        """Schedule an action to be scheduled after this Action

        The dt argument can be given to delay the chained action by the
        specified time.

        If this action has already been called, the chained action is scheduled
        immediately `dt` units after the current time.
        To prevent or modify this behavior, the caller can check the `expired`
        attribute.

        Returns the chained action.
        """
        if self.expired:
            self.clock.schedule(action, dt)
        else:
            self._chain.append((action, dt))
        return action

    @classmethod
    def coerce(cls, value):
        """Coerce a value into an action

        Wraps functions in FunctionCallers, and numbers in Delays
        """
        if isinstance(value, Action):
            return value
        elif callable(value):
            return FunctionCaller(value)
        elif isinstance(value, numbers.Real):
            return Delay(value)
        else:
            raise ValueError("%s can't be coerced into Action" % value)

    def __call__(self):
        """Run this action.

        Subclasses that represent discrete moments in time should call the
        superclass implementation when they are finished running.

        Subclasses that represent time intervals (there's a delay between
        the moment they are called and when they trigger chained actions)
        should call `expire()` when they are called, and `triggr_chain()` when
        they're done.
        """
        self.expire()
        self.trigger_chain()

    def expire(self):
        if self.expired:
            raise RuntimeError('%s was run twice' % self)
        self.expired = True

    def trigger_chain(self):
        """Schedule the chained actions.
        """
        for dt, chained in self._chain:
            self.clock.schedule(dt, chained)

    def schedule_callback(self, clock, time):
        """Called from a clock when this Action is scheduled"""
        if self.clock:
            raise RuntimeError('%s was scheduled twice' % self)
        self.clock = clock
        self.scheduled_time = time

    def __add__(self, other):
        try:
            other = self.coerce(other)
        except ValueError:
            return NotImplemented
        return Sequence(self, other)

    def __radd__(self, other):
        try:
            other = self.coerce(other)
        except ValueError:
            return NotImplemented
        return Sequence(other, self)

    def __or__(self, other):
        try:
            other = self.coerce(other)
        except ValueError:
            return NotImplemented
        return Parallel(self, other)

    def __ror__(self, other):
        try:
            other = self.coerce(other)
        except ValueError:
            return NotImplemented
        return Parallel(other, self)

class FunctionCaller(Action):
    """An Action that calls the given function, passing it the args and kwargs
    """
    def __init__(self, function, *args, **kwargs):
        super(FunctionCaller, self).__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        self.function(*self.args, **self.kwargs)
        super(FunctionCaller, self).__call__()

class Delay(Action):
    """An Action that triggers chained actions after a given delay
    """
    def __init__(self, time):
        super(Delay, self).__init__()
        self.time = time

    def __call__(self):
        self.expire()
        self.clock.schedule(self.trigger_chain, self.time)

class Sequence(Action):
    """An Action that runs a series of Actions one after the other
    """
    def __init__(self, *actions, **kwargs):
        super(Sequence, self).__init__(**kwargs)
        self.remaining_actions = list(actions)
        self.remaining_actions.reverse()

    def __call__(self):
        self.expire()
        self.call_next()

    def call_next(self):
        try:
            action = self.remaining_actions.pop()
        except:
            self.trigger_chain()
        else:
            action.chain(self.call_next)
            self.clock.schedule(action)

class Parallel(Action):
    """Starts the given Actions, and triggers chained ones after all are done

    That is, after all the given actions have triggered their chained actions,
    Parallel triggers its own chained actions.
    """
    def __init__(self, *actions, **kwargs):
        self.remaining_actions = actions
        super(Parallel, self).__init__(**kwargs)

    def __call__(self):
        print 'Calling', self, self.remaining_actions
        self.expire()
        for action in self.remaining_actions:
            def triggered(action=action):
                self.triggered(action)
            action.chain(triggered)
            self.clock.schedule(action)
        self.remaining_actions = set(self.remaining_actions)

    def triggered(self, action):
        self.remaining_actions.remove(action)
        if not self.remaining_actions:
            self.trigger_chain()
