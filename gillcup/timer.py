
import heapq
import collections

from gillcup.action import FunctionAction


EventHeapEntry = collections.namedtuple(
        'EventHeapEntry',
        'time index action'
    )


class Timer(object):
    """Keeps track of time.

    Use advance() to push time forward.
    This is done manually to allow non-realtime simulations/renders.
    Time can only be moved forward, because events can change state.

    Use schedule() to schedule an event for the future.
    """
    def __init__(self, time=0):
        self.events = []
        self.time = time
        self.currentEventIndex = 0

    def advance(self, dt):
        if dt < 0:
            raise ValueError("Can't advance into the past")
        while self.events and self.events[0].time <= self.time + dt:
            entry = heapq.heappop(self.events)
            dt -= entry.time - self.time
            self.time = entry.time
            entry.action.run(self)
        self.time += dt

    def schedule(self, dt, *actions):
        if dt < 0:
            raise ValueError("Can't schedule an event in the past")
        for action in actions:
            if callable(action):
                action = FunctionAction(action)
            heapq.heappush(self.events, EventHeapEntry(
                    self.time + dt,
                    self.currentEventIndex,
                    action,
                ))
            self.currentEventIndex += 1
