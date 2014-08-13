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
    :param duration: The duration of the animation
    :param clock: The :class:`~gillcup.clock.Clock` that controls the
                  animation's time
    :param delay: Time at which the animation starts
    :param infinite: If false, the animation starts at :token:`delay` time
                     units after :func:`anim` is called,
                     and ends :token:`duration` time units after it starts.
                     Outside of this time interval, the value is clamped at
                     :token:`start` (before) or :token:`end` (after).

                     If true, animation is not clamped.
                     Outside of the mentioned interval, the value is
                     extrapolated past :token:`start` and :token:`end`.
    """
    progress = Progress(clock, duration, delay=delay, clamp=not infinite)
    return Interpolation(start, end, progress)
