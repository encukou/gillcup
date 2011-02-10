# Encoding: UTF-8

"""
In Gillcup, animation means two things: running code at specified times and
changing object properties with time.

You will notice that the preceding sentence mentions time quite a lot. But what
is this time?

You could determine time by looking at the computer's clock, but that would
only work with real-time animations. When you'd want to render a movie,
where each frame takes 2 seconds to draw and there are 25 frames per second,
you'd be stuck.

That's why Gillcup introduces a flexible source of time: Timers. These are
objects with three attributes:

-  time, which gives the current time (“now”) on the timer,
-  advance(dt), which advances the timer by “dt” units, and
-  schedule(dt, action), which schedules an “action” to happen “dt” time units
   from “now”


Obtaining timers
................

The run() function from graphics.mainwindow automatically creates a timer that
is tied to the system clock (or, rather, the Pyglet clock; this means it won't
run if the Pyglet main loop is not running); this is a singleton that can be
obtained through the mainwindow.getMainTimer() function.

New timers can be created by instantiating the gillcup.timer.Timer class; of
course, you must call advance() on these manually.


Timers and layers
.................

Each graphics object can have its timer, which is used for animations.
It can be set as the “timer” argument to __init__; if left out, the object
inherits its parent timer. It can be changed by setting the “timer” attribute.

If an object has no timer and an animation is requested on it, it searches up
through its parent and its descendants before it dies with an error, and the
mainwindow convenience functions automatically set the root layer's timer
if one's not set.

An object doesn't actually need the timer itself; it is only used when creating
animations on it. Even then, a different timer can be specified. However,
having the timer available is very convenient.

Module Contents
...............
"""

import heapq
import collections
import weakref

from gillcup.action import FunctionAction


_EventHeapEntry = collections.namedtuple(
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
        """Call to advance the timer

        Steps the timer dt units to the future, running any scheduled Actions.
        """
        if dt < 0:
            raise ValueError("Can't advance into the past")
        while self.events and self.events[0].time <= self.time + dt:
            entry = heapq.heappop(self.events)
            dt -= entry.time - self.time
            self.time = entry.time
            entry.action.run(self)
        self.time += dt

    def schedule(self, dt, *actions):
        """Schedule actions to run "dt" time units from the current time

        Scheduling is stable:  if two things are scheduled for the same
        time, they will be called in the order they were scheduled.
        """
        if dt < 0:
            raise ValueError("Can't schedule an event in the past")
        for action in actions:
            if callable(action):
                action = FunctionAction(action)
            if action in pastActions:
                raise AssertionError('Scheduling an action twice!')
            pastActions[action] = True
            heapq.heappush(self.events, _EventHeapEntry(
                    self.time + dt,
                    self.currentEventIndex,
                    action,
                ))
            self.currentEventIndex += 1

pastActions = weakref.WeakKeyDictionary()
