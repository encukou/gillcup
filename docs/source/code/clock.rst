gillcup.clock
=============

.. module:: gillcup.clock

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

.. autoclass:: gillcup.Clock

    Basic methods:

        .. automethod:: gillcup.Clock.advance
        .. automethod:: gillcup.Clock.schedule

    Update function registration:

        .. automethod:: gillcup.Clock.schedule_update_function
        .. automethod:: gillcup.Clock.unschedule_update_function

.. autoclass:: gillcup.Subclock
    :members: speed
