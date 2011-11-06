# Encoding: UTF-8

import collections
import weakref
import heapq

_HeapEntry = collections.namedtuple('EventHeapEntry', 'time index action')

class Clock(object):
    """Keeps track of time.

    In Gillcup, animation means two things: running code at specified times,
    and changing object properties with time.

    You will notice that the preceding sentence mentions time quite a lot. But
    what is this time?

    You could determine time by looking at the computer's clock, but that would
    only work with real-time animations. When you'd want to render a movie,
    where each frame takes 2 seconds to draw and there are 25 frames per
    second, you'd be stuck.

    That's why Gillcup introduces a flexible source of time: the Clock. This is
    an objects with three basic attributes:

    -  time, which gives the current time (“now”) on the clock,
    -  advance(dt), which advances the timer by “dt” units, and
    -  schedule(dt, action), which schedules “action” to be called “dt” time
       units from the current time.

    What a “time unit” means is entirely up to the application – it could be
    seconds, movie/simulation frames, etc.
    """
    def __init__(self, time=0):
        # Time on the clock
        self.time = time

        # Next action index; used to keep FIFO ordering for actions scheduled
        # for the same time
        self.next_index = 0

        # Heap queue of scheduled actions
        self.events = []

        # Update functions (see `schedule_update_function`)
        self.update_functions = WeakSet()

    def advance(self, dt):
        """Call to advance the clock's time

        Steps the clock dt units to the future, pausing at times when actions
        are scheduled, and running them.

        Attempting to move to the past (dt<0) will raise an error.
        """
        if dt < 0:
            raise ValueError('Moving backwards in time')
        while self.events and self.events[0].time <= self.time + dt:
            entry = heapq.heappop(self.events)
            dt -= entry.time - self.time
            previous_time = self.time
            self.time = entry.time
            if previous_time != self.time:
                self._run_update_functions()
            entry.action()
        self.time += dt
        self._run_update_functions()

    def schedule(self, action, dt=0):
        """Schedule an action to be run "dt" time units from the current time

        Scheduling is stable:  if two things are scheduled for the same
        time, they will be called in the order they were scheduled.

        Scheduling an action in the past (dt<0) will raise an error.

        If the scheduled callable has a “schedule_callback” method, it will
        be called with the clock and the time it'd been scheduled at.
        """
        if dt < 0:
            raise ValueError('Scheduling an action in the past')
        self.next_index += 1
        scheduled_time = self.time + dt
        entry = _HeapEntry(scheduled_time, self.next_index, action)
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

try:
    WeakSet = weakref.WeakSet
except AttributeError:
    class WeakSet(weakref.WeakKeyDictionary):
        """Stripped-down WeakSet implementation for Python 2.6

        (only defines the methods we need)
        """
        def add(self, item):
            self[item] = None

        def discard(self, item):
            self.pop(item)
