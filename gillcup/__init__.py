"""
Gillcup is based on three concepts:

*   The :mod:`~gillcup.clock` provides a customizable, discrete-time event
    system, based on futures and coroutines of Python's :mod:`asyncio` library.
*   The :mod:`~gillcup.expressions` make it possible to define and evaluate
    numeric expressions based on external factors such as Clock time.
*   The :mod:`~signals` enable notifications.

"""

def coroutine(func):
    return func
