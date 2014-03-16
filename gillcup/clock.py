import collections
import heapq
import asyncio

import gillcup.futures

_Event = collections.namedtuple('EventHeapEntry', 'time index callback args')

# Next action index; used to keep FIFO ordering for actions scheduled
# for the same time
next_index = 0


class Clock:
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

    def _get_next_event(self):
        try:
            event = self.events[0]
        except IndexError:
            events = []
        else:
            events = [(event.time - self.time, event.index, self, event)]
        for subclock in self._subclocks:
            event = subclock._get_next_event()
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

    @asyncio.coroutine
    def advance(self, dt, *, _continuing=False):
        """Call to advance the clock's time

        Steps the clock dt units to the future, pausing at times when actions
        are scheduled, and running them.

        Attempting to move to the past (dt<0) will raise an error.
        """
        print(self.advancing, _continuing)
        if self.advancing and not _continuing:
            raise RuntimeError('Clock.advance called recursively')
        dt *= self.speed
        if dt < 0:
            raise ValueError('Moving backwards in time')
        self.advancing = True

        event = self._get_next_event()
        if event is not None:
            event_dt, _index, clock, event = event
        if event is None or event_dt > dt:
            if dt:
                self._advance(dt)
            dt = 0
            self.advancing = False
        else:
            if event_dt:
                self._advance(event_dt)
            dt -= event_dt
            _evt = heapq.heappop(clock.events)
            assert _evt is event and clock.time == event.time
            # jump to the event's time
            clock.time = event.time
            # Handle the event (synchronously!)
            event.callback(*event.args)

            # finish jumping to target time
            yield from asyncio.Task(self.advance(dt, _continuing=True))

        print('Done.', _continuing)

    def advance_sync(self, dt):
        """Call (and wait for) self.advance() outside of an event loop"""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.advance(dt))

    def _advance(self, dt):
        self.time += dt
        for subclock in self._subclocks:
            subclock._advance(dt * subclock.speed)

    def sleep(self, delay):
        """Return a future that will complete after "dt" time units

        Scheduling for the past (dt<0) will raise an error.
        """
        future = asyncio.Future()
        self.schedule(delay, future.set_result, None)
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

    def schedule(self, delay, callback, *args):
        """Schedule callback to be called after "dt" time units
        """
        global next_index
        if delay < 0:
            raise ValueError('Scheduling an action in the past')
        next_index += 1
        scheduled_time = self.time + delay
        event = _Event(scheduled_time, next_index, callback, args)
        heapq.heappush(self.events, event)

    def task(self, coro):
        @asyncio.coroutine
        def coro_wrapper():
            iterator = iter(coro)
            value = exception = None
            while True:
                if exception is None:
                    value = iterator.send(value)
                else:
                    value = iterator.throw(exception)
                print('Got', value)
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
