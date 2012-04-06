# Encoding: UTF-8
"""Gillcup's Clock Class

In Gillcup, animation means two things: running code at specified times,
and changing object properties with time.

You will notice that the preceding sentence mentions time quite a lot. But
what is this time?

You could determine time by looking at the computer's clock, but that would
only work with real-time animations. When you'd want to render a movie,
where each frame takes 2 seconds to draw and there are 25 frames per
second, you'd be stuck.
That's why Gillcup introduces a flexible source of time, the Clock, which
keeps track of time and schedules actions.

Time is measured in “time units”.
What a time unit means is entirely up to the application – it could be
seconds, movie/simulation frames, etc.
"""

from __future__ import unicode_literals, division, print_function

import collections
import weakref
import heapq

from gillcup.properties import AnimatedProperty

_HeapEntry = collections.namedtuple('EventHeapEntry', 'time index action')

# Next action index; used to keep FIFO ordering for actions scheduled
# for the same time
next_index = 0


class Clock(object):
    """Keeps track of time and schedules events.

    Attributes:

        .. attribute:: time

            The current time on the clock. Never assign to it directly;
            use :meth:`~gillcup.Clock.advance()` instead.
    """
    def __init__(self):
        # Time on the clock
        self.time = 0

        # Heap queue of scheduled actions
        self.events = []

        # Update functions (see `schedule_update_function`)
        self.update_functions = WeakSet()

        # Recursion guard flag for advance()
        self.advancing = False

        # List of dependent clocks
        self._subclocks = set()

    @property
    def _next_event(self):
        try:
            event = self.events[0]
            events = [(event.time - self.time, event.index, self, event)]
        except IndexError:
            events = []
        for subclock in self._subclocks:
            event = subclock._next_event  # pylint: disable=W0212
            if event:
                remain, index, clock, event = event
                try:
                    remain /= subclock.speed
                except ZeroDivisionError:
                    # zero speed – events never happen
                    pass
                else:
                    events.append((remain, index, clock, event))
        try:
            return min(events)
        except ValueError:
            return None

    def advance(self, dt):
        """Call to advance the clock's time

        Steps the clock dt units to the future, pausing at times when actions
        are scheduled, and running them.

        Attempting to move to the past (dt<0) will raise an error.
        """
        if dt < 0:
            raise ValueError('Moving backwards in time')
        if self.advancing:
            raise RuntimeError('Clock.advance called recursively')
        self.advancing = True
        try:
            while True:
                event = self._next_event
                if not event:
                    break
                event_dt, _index, clock, event = event
                if event_dt > dt:
                    break
                if dt:
                    self._advance(event_dt)
                    self._run_update_functions()
                dt -= event_dt
                _evt = heapq.heappop(clock.events)
                assert _evt is event and clock.time == event.time
                clock.time = event.time
                event.action()
            if dt:
                self._advance(dt)
                self._run_update_functions()
        finally:
            self.advancing = False

    def _advance(self, dt):
        self.time += dt
        for subclock in self._subclocks:
            subclock._advance(dt * subclock.speed)  # pylint: disable=W0212

    def schedule(self, action, dt=0):
        """Schedule an action to be run "dt" time units from the current time

        Scheduling is stable:  if two things are scheduled for the same
        time, they will be called in the order they were scheduled.

        Scheduling an action in the past (dt<0) will raise an error.

        If the scheduled callable has a “schedule_callback” method, it will
        be called with the clock and the time it's been scheduled at.
        """
        global next_index
        if dt < 0:
            raise ValueError('Scheduling an action in the past')
        next_index += 1
        scheduled_time = self.time + dt
        entry = _HeapEntry(scheduled_time, next_index, action)
        heapq.heappush(self.events, entry)
        try:
            schedule_callback = action.schedule_callback
        except AttributeError:
            pass
        else:
            schedule_callback(self, scheduled_time)

    def schedule_update_function(self, function):
        """Schedule a function to be called every time the clock advances

        Then function will be called a lot, so it shouldn't be very expensive.

        Only a weak reference is made to the function, so the caller should
        ensure another reference to it is retained as long as it should be
        called.
        """
        self.update_functions.add(function)

    def unschedule_update_function(self, function):
        """Unschedule a function scheduled by `schedule_update_function`
        """
        # Don't raise an error if the function is no longer there – we're
        # dealing with weakrefs.
        self.update_functions.discard(function)

    def _run_update_functions(self):
        for update_function in list(self.update_functions):
            update_function()
        for subclock in self._subclocks:
            subclock._run_update_functions()  # pylint: disable=W0212


class Subclock(Clock):
    """A Clock that advances in sync with another Clock

    A Subclock advances whenever its *parent* clock does.
    It has a `speed` attribute, which specifies the relative speed relative to
    the parent clock. For example, if speed==2, the subclock will run twice as
    fast as its parent clock.

    Unlike clocks synchronized via actions or update functions, the actions
    scheduled on a parent Clock and all subclocks are run in the correct
    sequence, with all clocks at the correct times when each action is run.
    """
    speed = AnimatedProperty(1, docstring="""Speed of the clock.

    The speed is an AnimatedProperty. When changing, beware that it is only
    checked when advance() is called or when a scheduled action is run,
    so speed animations will be only approximate.
    For better accuracy, call :meth:`~gillcup.Clock.advance`
    with small *dt*, or schedule a periodic dummy action at small inervals.
    """)

    def __init__(self, parent, speed=1):
        super(Subclock, self).__init__()
        self.speed = speed
        parent._subclocks.add(self)  # pylint: disable=W0212


try:  # pragma: no cover
    WeakSet = weakref.WeakSet  # pylint: disable=E1101
except AttributeError:  # pragma: no cover

    class WeakSet(weakref.WeakKeyDictionary):
        """Stripped-down WeakSet implementation for Python 2.6

        (only defines the methods we need)
        """
        def add(self, item):
            """Add an item to the set"""
            self[item] = None

        def discard(self, item):
            """Remove an item from the set"""
            self.pop(item)
