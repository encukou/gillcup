# Encoding: UTF-8

from gillcup.chaining import Chainable

class Action(Chainable):
    """A discrete event.

    As any callable, an Action can be scheduled on a clock, either by calling
    schedule(), or directly in the constructor.

    Other actions (the lowercase term denotes “arbitrary callables”) may be
    chained to an Action, that is, scheduled to run at some time after the
    Action is run.

    Each Action may only be scheduled once. Initializing the class with the
    `clock` and `dt` arguments counts as scheduling.
    """
    def __init__(self, clock=None, dt=0):
        super(Action, self).__init__()

        # Set to True once the Action runs
        self.expired = False

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
            return action
        else:
            return super(Action, self).chain(action, dt)

    def __call__(self):
        """Run this action.

        Subclasses should call the superclass implementation when they are
        finished running.
        """
        if self.expired:
            raise RuntimeError('%s was run twice' % self)
        self.expired = True
        self.trigger_chain(self.clock)

    def schedule_callback(self, clock, time):
        """Called from a clock when this Action is scheduled"""
        if self.clock:
            raise RuntimeError('An Action was scheduled twice')
        self.clock = clock
        self.scheduled_time = time

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
        self.clock.schedule(super(Delay, self).__call__, self.time)
