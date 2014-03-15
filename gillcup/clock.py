import collections
import heapq
import asyncio

_Event = collections.namedtuple('EventHeapEntry', 'time index callback args')

# Next action index; used to keep FIFO ordering for actions scheduled
# for the same time
next_index = 0


class Clock(object):
    """Keeps track of discrete time, and schedules events.

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

        # Recursion guard flag for advance()
        self.advancing = False

        # Set of dependent clocks
        self._subclocks = set()

    speed = 1

    @property
    def _next_event(self):
        try:
            event = self.events[0]
        except IndexError:
            events = []
        else:
            events = [(event.time - self.time, event.index, self, event)]
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
        dt *= self.speed
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
                dt -= event_dt
                _evt = heapq.heappop(clock.events)
                assert _evt is event and clock.time == event.time
                clock.time = event.time
                event.callback(*event.args)
            if dt:
                self._advance(dt)
        finally:
            self.advancing = False

    def _advance(self, dt):
        self.time += dt
        for subclock in self._subclocks:
            subclock._advance(dt * subclock.speed)  # pylint: disable=W0212

    def wait(self, dt):
        """Return a future representing a wait of "dt" time units
        """
        future = asyncio.Future()
        self.schedule(dt, future.set_result, self)

    def schedule(self, dt, callback, *args):
        """Schedule a callback to be called `dt` time units in the future

        Scheduling is stable: if two callbacks are scheduled for the same
        time, they will be called in the order they were scheduled.

        Scheduling for the past (dt<0) will raise an error.
        """
        global next_index
        if dt < 0:
            raise ValueError('Scheduling an action in the past')
        next_index += 1
        scheduled_time = self.time + dt
        event = _Event(scheduled_time, next_index, callback, args)
        heapq.heappush(self.events, event)


class Subclock(Clock):
    """A Clock that advances in sync with another Clock

    A Subclock advances whenever its *parent* clock does.
    Its `speed` attribute specifies the relative speed relative to the parent
    clock. For example, if speed==2, the subclock will run twice as fast as its
    parent clock.

    The actions scheduled on a parent Clock and all subclocks are run in the
    correct sequence, with consistent times on the clocks.
    """

    def __init__(self, parent, speed=1):
        super(Subclock, self).__init__()
        self.speed = speed
        parent._subclocks.add(self)  # pylint: disable=W0212
