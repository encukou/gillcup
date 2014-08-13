"""
TODO: Write the docs

Reference
---------

.. autofunction:: anim

"""

from gillcup.expressions import Interpolation, Progress


def anim(start, end, duration, clock, *, delay=0, infinite=False):
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
    :param infinite: If false, the animation starts at :token:`delay` time
                     units after :func:`anim` is called,
                     and ends :token:`duration` time units after it starts.
                     Outside of this time interval, the value is clamped at
                     :token:`start` (before) or :token:`end` (after).

                     If true, animation is not clamped.
                     Outside of the mentioned interval, the value is
                     extrapolated past :token:`start` or :token:`end`.
    """
    if duration < 0:
        start, end = end, start
        duration = -duration
        delay -= duration
    progress = Progress(clock, duration, delay=delay, clamp=not infinite)
    return Interpolation(start, end, progress)
