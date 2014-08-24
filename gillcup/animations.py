"""Animation helpers

This module builds on the building blocks in :mod:`~gillcup.expressions` and
:mod:`~gillcup.properties` to provide higher-level animation utilities.

Reference
---------

.. autofunction:: anim

"""

import asyncio

from gillcup.expressions import Interpolation, Progress, Elementwise
from gillcup.expressions import Expression
from gillcup import easings


class _Anim(Expression):
    """An expression with a "done" future

    An :class:`~gillcup.expressions.Expression` with a :attr:`done` attribute,
    which is a :class:`~asyncio.Future` that becomes done when an animation
    is finished.
    """
    def __init__(self, parent, done):
        self.done = done
        self.replacement = parent

    def get(self):
        return self.replacement.get()

    @property
    def children(self):
        yield self.replacement


def anim(start, end, duration, clock, *,
         delay=0, easing=None, infinite=False, strength=1):
    """Create an animated expression

    Returns an expression that morphs between :token:`start` and :token:`end`
    values during :token:`duration` time units on the given :token:`clock`.

    At its simplest, animation is a simple combination of the
    :class:`~gillcup.expressions.Interpolation` and
    :class:`~gillcup.expressions.Progress` expressions.
    This function wraps creating them in an easy-to-use package,
    with a few extra frills on top.

    The resulting animation is scheduled as soon as it is created.

    :param start: The value at the start
    :param end: The value at the end
    :param duration: The duration of the animation.

                     If negative, the animation runs in reverse, starting
                     :token:`delay` + :token:`duration` time units from now
                     (which is less than :token:`delay`),
                     and ending :token:`delay` units from now.

                     If zero, :token:`delay` time units from now the value
                     changes abruptly from :token:`start` to :token:`end`.
                     In this case, :token:`infinite` must be false.
    :param clock: The :class:`~gillcup.clock.Clock` that controls the
                  animation's time
    :param delay: Time from now at which the animation starts
    :param easing: An easing to apply. This should be a pure function.
                   The value is passed to
                   :func:`easings.get <gillcup.easings.get>`, so it can
                   be a string naming one of the standard easings.

                   None specifies an identity funcion (i.e. linear easing).
    :param infinite: If false, the animation starts at :token:`delay` time
                     units after :func:`anim` is called,
                     and ends :token:`duration` time units after it starts.
                     Outside of this time interval, the value is clamped at
                     :token:`start` (before) or :token:`end` (after).

                     If true, animation is not clamped.
                     Outside of the mentioned interval, the value is
                     extrapolated past :token:`start` or :token:`end`.
    :param strength: The strength of the effect:
                     if 0, the value always stays at :token:`start`;
                     if 1, it is animated normally.

    :return: An expression with a :attr:`~Anim.done` attribute, which
             contains a future that is done when this animation finishes.
             The future is tied to the :token:`clock`.
    """
    if duration < 0:
        start, end = end, start
        duration = -duration
        delay -= duration

    if delay + duration < 0:
        future = asyncio.Future()
        future.set_result(True)
        done = clock.wait_for(future)
    else:
        done = clock.sleep(delay + duration)

    progress = Progress(clock, duration, delay=delay, clamp=not infinite)
    if easing:
        easing_func = easings.get(easing)
        progress = Elementwise(progress, easing_func)
    interp = Interpolation(start, end, progress * strength)
    return _Anim(interp, done)
