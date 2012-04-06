# Encoding: UTF-8

"""Gillcup Actions

Although arbitrary callables can be scheduled on a Gillcup
:class:`~gillcup.Clock`, one frequently schedules objects that are specifically
made for this purpose.
Using :class:`gillcup.Action` allows one to chain actions together in various
ways, allowing the developer to create complex effects.
"""

from __future__ import unicode_literals, division, print_function

import numbers
import functools

from six import callable, advance_iterator  # pylint: disable=W0622


class Action(object):
    """A chainable “event” designed for being scheduled.

    As any callable, an Action can be scheduled on a clock, either by
    :meth:`~gillcup.Clock.schedule()`, or by chaining, or, as a shortcut,
    directly from the constructor with the `clock` and `dt` arguments.
    Each Action may only be scheduled *once*.

    Other actions (the lowercase term denotes “arbitrary callables”) may be
    chained to an Action, that is, scheduled to run at some time after the
    Action is run.

    Some Actions may represent a time interval or process rather than a
    discrete point in time. In these cases, chained actions are run after the
    interval is over or the process finishes.

    Actions may be combined to form larger structures using
    :ref:`helper Action subclasses <action-building-blocks>` as building
    blocks.
    As a shorthand, the following operators are available:

        *   ``+`` creates a :class:`~gillcup.actions.Sequence` of actions;
            one is run after the other.
        *   ``|`` creates a :class:`~gillcup.actions.Parallel` construct:
            all actions are started at once.

    The operators can be used with regular callables (which are wrapped in
    :class:`~gillcup.actions.FunctionCaller`), or with numbers
    (which create corresponding :class:`delays <gillcup.actions.Delay>`), or
    with iterables (which get wrapped in :class:`~gillcup.actions.Process`).
    """
    # The states an Animation goes through are:
    # - unscheduled (self.clock is unset)
    # - scheduled
    # - in progress (self.expired == True)
    # - done (self.chain_triggered == True)
    scheduled_time = None

    def __init__(self, clock=None, dt=0):
        super(Action, self).__init__()

        # Set to True once the Action runs
        self.expired = False

        # Set to True once chained actions are scheduled
        self.chain_triggered = False

        # The chained actions
        self._chain = []

        # The clock
        self.clock = None
        if clock:
            clock.schedule(self, dt)
        elif dt != 0:
            # We're not scheduling yet, so dt would be ignored
            raise ValueError('dt specified without a clock')

    def chain(self, action, dt=0):
        """Schedule an action to be scheduled after this Action

        The dt argument can be given to delay the chained action by the
        specified time.

        If this Action has already been called, the chained action is scheduled
        immediately `dt` units after the current time.
        To prevent or modify this behavior, the caller can check the
        :attr:`~gillcup.Action.chain_triggered` attribute.

        Returns the chained action.
        """
        if self.chain_triggered:
            self.clock.schedule(action, dt)
        else:
            self._chain.append((action, dt))
        return action

    @classmethod
    def coerce(cls, value):
        """Coerce value into an action. Called on operands of ``+`` and ``|``.

        Wraps functions in FunctionCallers, and numbers in Delays
        """
        if isinstance(value, Action):
            return value
        elif callable(value):
            return FunctionCaller(value)
        elif isinstance(value, numbers.Real):
            return Delay(value)
        else:
            try:
                iterator = iter(value)
            except TypeError:
                raise ValueError("%s can't be coerced into Action" % value)
            else:
                return Process(iterator)

    def __call__(self):
        """Run this action.

        Subclasses that represent discrete moments in time should call the
        superclass implementation when they are finished running.

        Subclasses that represent time intervals (there's a delay between
        the moment they are called and when they trigger chained actions)
        should call :meth:`~gillcup.Action.expire` when they are called,
        and :meth:`~gillcup.Action.trigger_chain` when they're done.
        """
        self.expire()
        self.trigger_chain()

    def expire(self):
        """Marks the Action as run.

        Subclasses must call this method at the start of
        :meth:`~gillcup.Action.__call__`.
        """
        if self.expired:
            raise RuntimeError('%s was run twice' % self)
        self.expired = True

    def trigger_chain(self):
        """Schedule the chained actions.

        Subclasses must call this method after the Action runs; see
        :meth:`~gillcup.Action.__call__`.
        """
        self.chain_triggered = True
        for dt, chained in self._chain:
            self.clock.schedule(dt, chained)
        self._chain = []

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
    """An Action that calls given `function`, passing `args` and `kwargs` to it

    `function` can be any callable.
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

    The `kwargs` are passed to :class:`gillcup.Action`'s initializer.
    """
    def __init__(self, time, **kwargs):
        super(Delay, self).__init__(**kwargs)
        self.time = time

    def __call__(self):
        self.expire()
        self.clock.schedule(self.trigger_chain, self.time)


class Sequence(Action):
    """An Action that runs a series of Actions one after the other

    Actions chained to a Sequence are triggered after the last Action in the
    sequence.

    The `kwargs` are passed to :class:`gillcup.Action`'s initializer.
    """
    def __init__(self, *actions, **kwargs):
        super(Sequence, self).__init__(**kwargs)
        self.remaining_actions = list(actions)
        self.remaining_actions.reverse()

    def __call__(self):
        self.expire()
        self._call_next()

    def _call_next(self):
        try:
            action = self.remaining_actions.pop()
        except IndexError:
            self.trigger_chain()
        else:
            action.chain(self._call_next)
            self.clock.schedule(action)

    # XXX: Overload __add__, __radd__?


class Parallel(Action):
    """Starts the given Actions, and triggers chained ones after all are done

    That is, after all the given actions have triggered their chained actions,
    Parallel triggers its own chained actions.

    The `kwargs` are passed to :class:`gillcup.Action`'s initializer.
    """
    def __init__(self, *actions, **kwargs):
        self.remaining_actions = actions
        super(Parallel, self).__init__(**kwargs)

    def __call__(self):
        self.expire()
        for action in self.remaining_actions:
            def _triggered(action=action):
                self._triggered(action)
            action.chain(_triggered)
            self.clock.schedule(action)
        self.remaining_actions = set(self.remaining_actions)

    def _triggered(self, action):
        self.remaining_actions.remove(action)
        if not self.remaining_actions:
            self.trigger_chain()

    # XXX: Overload __or__, __ror__?


class Process(Action):
    """Wraps the given iterable

    When triggered, takes an item from the iterable and schedules it, then
    chains the scheduling of the next item, and so on.
    When the underlying iterator is exhausted, chained actions are run.

    The items in the underlying iterable can be callables, numbers or other
    iterables, as for :class:`~gillcup.actions.Action`'s ``+`` and ``|``
    operators.

    The `kwargs` are passed to :class:`gillcup.Action`'s initializer.

    See :func:`process_generator` for a simple way to create Processes.
    """
    def __init__(self, iterable, **kwargs):
        self.iterator = iter(iterable)
        super(Process, self).__init__(**kwargs)

    def __call__(self):
        self.expire()
        self.do_next()

    def do_next(self):
        """Schedule the next thing from the iterable"""
        try:
            value = advance_iterator(self.iterator)
        except StopIteration:
            self.trigger_chain()
        else:
            action = self.coerce(value)
            action.chain(self.do_next)
            self.clock.schedule(action)


def process_generator(func):
    """Decorator for creating :class:`~gillcup.actions.Process`\ es

    Used as a decorator on a generator function, it allows writing in a
    declarative style instead of callbacks, with ``yield`` statements for
    "asynchronousness".
    """
    @functools.wraps(func)
    def _f(*args, **kwargs):
        return Process(func(*args, **kwargs))
    return _f
