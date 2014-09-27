"""Asyncio-based discrete-time simulation infrastructure

A clock keeps track of *time*. But, what is time?

If you are familiar with the :mod:`asyncio` library,
you might know the :func:`asyncio.sleep` coroutine.
It "sleeps" roughly for a given number of seconds,
usually based on the computer's system time.
Since the Python process does not control this time, ``sleep()`` may sleep
longer than requested if the event loop is busy.
Also, the system time always changes:
so it is not possible to do two actions at exactly the same time.
For animations and simulations, such time is unusable.
Thus, time in Gillcup is a very different beast.

Gillcup time is a quantity that *increases in discrete intervals*.
On other words, it can never go backwards,
and it does not change while animation/simulation code is executing.

You can schedule an function for any time in the future.
When the clock advances to that time, the clock is frozen at the event's
scheduled time, and the function is called.

The passage of Gillcup time is entirely in control of the programmer.
It can be tied to the system clock to produce real-time animations,
it can be slowed down or sped up,
or an entire simulation can be run at once to get simulation results quickly.

The Clock runs inside an asyncio event loop,
using the future, callback, and coroutine mechanisms familiar to asyncio users.
Gillcup uses its own :class:`~gillcup.futures.Future` objects that are tied
to a clock that handles them.
Any callbacks on a Gillcup future are handled by that future's clock;
the Gillcup time does not advance between the future's completion
and the callback execution.

A coroutine can be scheduled on a Gillcup clock using
:meth:`~gillcup.clocks.Clock.task`; see the corresponding docs for details.


Reference
---------

.. autofunction:: gillcup.clocks.coroutine
.. autoclass:: gillcup.clocks.Clock
.. autoclass:: gillcup.clocks.Subclock
"""

import collections
import heapq
import asyncio

import gillcup.futures
from gillcup.util.signature import fix_public_signature
from gillcup import expressions


def coroutine(func):
    """Mark a function as a Gillcup coroutine.

    Direct equivalent of :func:`asyncio.coroutine` -- also does nothing
    (unless asyncio debugging is enabled).
    """
    return asyncio.coroutine(func)


_Event = collections.namedtuple('_Event',
                                'time category index callback args')
_Event.__doc__ = """
    Heap entry

    Namedtuple elements:

        .. attribute:: time

            The time for which the event is scheduled

        .. attribute:: category

            Category for sorting.
            Normal events have category of 0;
            the event that advance() creates to wait for has a category of 1
            to ensure other events at the same time have completed.

        .. attribute:: index

            Index for sorting.
            Unique to each _Event, asigned from a global counter.
            Used to keep FIFO ordering for actions scheduled for the same time.

        .. attribute:: callback

            The action to perform.

        .. attribute:: args

            Arguments to call :token:`callback` with.
"""

_next_index = 0


class Clock:
    """Keeps track of discrete time, and schedules events.

    Attributes:

        .. attribute:: time

            The current time on the clock. A read-only expression.

            Use :meth:`advance` to increase this value.

        .. attribute:: speed

            Arguments to :meth:`advance` are multiplied by this value.
            Usefull mainly for :class:`Subclock`.

    Methods:

        .. automethod:: schedule

        .. automethod:: wait_for

        .. automethod:: sleep

        .. automethod:: advance

        .. automethod:: advance_sync

        .. automethod:: task
    """
    def __init__(self):
        # Time on the clock
        self._time_value = 0

        # Heap queue of scheduled actions
        self.events = []

        # Recursion guard flag for advance()
        self.advancing = False

        # Set of dependent clocks
        self._subclocks = set()

    speed = 1

    @property
    def time(self):
        try:
            return self._time_exp
        except AttributeError:
            prop = self._time_exp = expressions.Time(self)
            return prop

    def _get_next_event(self):
        try:
            event = self.events[0]
        except IndexError:
            events = []
        else:
            events = [(event.time - self._time_value, event.category,
                       event.index, self, event)]
        for subclock in self._subclocks:
            event = subclock._get_next_event()
            if event:
                remain, category, index, clock, event = event
                try:
                    remain /= subclock.speed
                except ZeroDivisionError:
                    # zero speed – events never happen
                    pass
                else:
                    events.append((remain, category, index, clock, event))
        try:
            return min(events)
        except ValueError:
            return None

    @asyncio.coroutine
    @fix_public_signature
    def advance(self, delay, *, _continuing=False):
        """Advance the clock's time

        Moves the clock's time forward, pausing at times when
        actions are scheduled, and running them.

        :param delay: If :token:`delay` is a real number, move that many time
            units into the future.
            Attempting to move to the past (negative delay) will raise
            an error.

            If :token:`delay` is None, the Clock will advance until no more
            actions are scheduled on it.
            Note that with recurring events, ``advance(None)`` may
            never finish.

            Otherwise :token:`delay` should be a Future; in this case Clock
            will advance until either that future is done, or no more actions
            are scheduled.
        """
        if not _continuing:
            if self.advancing:
                raise RuntimeError('Clock.advance called recursively')
            if delay is None:
                delay = asyncio.Future()
            try:
                float(delay)
            except TypeError:
                # We want to wait for a *Gillcup* future on *this* clock,
                # with category 1
                delay = gillcup.futures.Future(self, delay, _category=1)
            else:
                if delay < 0:
                    raise ValueError('Moving backwards in time')
                delay = self.sleep(delay * self.speed, _category=1)
        self.advancing = True

        if delay.done():
            self.advancing = False
            return

        event = self._get_next_event()
        if event is None:
            self.advancing = False
            return

        event_dt, _cat, _index, clock, event = event
        if event_dt:
            self._advance(event_dt)
        _evt = heapq.heappop(clock.events)
        assert _evt is event and clock._time_value == event.time
        # jump to the event's time
        clock._time_value = event.time
        # Handle the event (synchronously!)
        event.callback(*event.args)

        # finish jumping
        yield from asyncio.Task(self.advance(delay, _continuing=True))

    def advance_sync(self, delay):
        """Call (and wait for) :meth:`advance` outside of an event loop

        Runs asyncio's main event loop until ``advance()`` is finished.

        Useful in testing or in some non-realtime applications.
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.advance(delay))

    def _advance(self, dt):
        self._time_value += dt
        for subclock in self._subclocks:
            subclock._advance(dt * subclock.speed)

    @fix_public_signature
    def sleep(self, delay, *, _category=0):
        """Return a future that will complete after "delay" time units

        Scheduling for the past (delay<0) will raise an error.
        """
        future = asyncio.Future()
        self.schedule(delay, future.set_result, None, _category=_category)
        return gillcup.futures.Future(self, future)

    def wait_for(self, future):
        """Wrap a future so that its calbacks are scheduled on this Clock

        Return a future that is done when the original one is,
        but any callbacks registered on it will be scheduled on this Clock.

        If the given future is already scheduling on this Clock,
        it is returned unchanged.
        """
        if isinstance(future, gillcup.futures.Future) and future.clock is self:
            return future
        else:
            return gillcup.futures.Future(self, future)

    @fix_public_signature
    def schedule(self, delay, callback, *args, _category=0):
        """Schedule callback to be called after "delay" time units
        """
        global _next_index
        if delay < 0:
            raise ValueError('Scheduling an action in the past')
        _next_index += 1
        scheduled_time = self._time_value + delay
        event = _Event(scheduled_time, _category, _next_index, callback, args)
        heapq.heappush(self.events, event)

    def task(self, coro):
        """Run an asyncio-style coroutine on this clock

        Futures yielded by the coroutine will be handled by this Clock.

        In addition to futures, the coroutine may yield real numbers,
        which are translated to :meth:`sleep`.
        """
        @asyncio.coroutine
        def coro_wrapper():
            iterator = iter(coro)
            value = exception = None
            while True:
                if exception is None:
                    value = iterator.send(value)
                else:
                    value = iterator.throw(exception)
                if value is None:
                    value = 0
                try:
                    try:
                        value = float(value)
                    except TypeError:
                        yield from self.wait_for(value)
                    else:
                        yield from self.sleep(value)
                except Exception as exc:
                    value = None
                    exception = exc
                except BaseException as exc:
                    iterator.throw(exc)
                    raise
        return asyncio.Task(coro_wrapper())


class Subclock(Clock):
    """A Clock that advances in sync with another Clock

    A Subclock advances whenever its :token:`parent` clock does.
    Its :token:`speed` attribute specifies the relative speed relative
    to the parent clock.
    For example, if ``speed==2``, the subclock will run twice as fast as its
    parent clock.

    The actions scheduled on a parent Clock and all subclocks are run in the
    correct sequence, with consistent times on the clocks.
    """

    def __init__(self, parent, speed=1):
        super(Subclock, self).__init__()
        self.speed = speed
        parent._subclocks.add(self)
