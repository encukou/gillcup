"""
TODO: Write the docs

Reference
---------

.. autofunction:: anim

"""

from gillcup.expressions import Interpolation, Progress


def anim(start, end, duration, clock):
    """Create an animated expression

    Returns an expression that morphs between :token:`start` and :token:`end`
    values during :token:`duration` time units on the given :token:`clock`.

    At its simplest, animation is a simple combination of the
    :class:`~gillcup.expressions.Interpolation` and
    :class:`~gillcup.expressions.Progress` expressions.
    This function wraps creating them in an easy-to-use package.

    :param start: The value at the start
    :param end: The value at the end
    :param duration: The duration of the animation
    :param clock: The :class:`~gillcup.clock.Clock` that controls the
                  animation's time
    """
    progress = Progress(clock, duration)
    return Interpolation(start, end, progress)
