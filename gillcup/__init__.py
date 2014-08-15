"""
Gillcup is based on three concepts:

*   The :mod:`~gillcup.clock` provides a customizable, discrete-time event
    system, based on futures and coroutines of Python's :mod:`asyncio` library.
*   The :mod:`~gillcup.expressions` make it possible to define and evaluate
    numeric expressions based on external factors such as Clock time.
*   The :mod:`~gillcup.signals` enable notifications.
*   The :mod:`~gillcup.easing` module contains tweening functions
    to spice up motion.

"""
import asyncio


def coroutine(func):
    """Mark a function as a Gillcup coroutine.

    Direct equivalent of :func:`asyncio.coroutine` -- also does nothing
    (unless asyncio debugging is enabled).
    """
    return asyncio.coroutine(func)
