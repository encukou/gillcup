"""A collection of functions that add flavor to motion.

The functions are based on Robert Penner's `Motion, Tweening, and Easing
<http://robertpenner.com/easing/>`_.
See his page for more background.

Each of the functions defined here can be used directly for an
“ease in” animation (one that speeds up over time).
For other types, use attributes: **out** (slows down over time), **in_out**
(speeds up, then slows down), and **out_in** (slows down, then speeds up).
The ease-in is also available in **in_**. For example,
``gillcup.easing.quad.in_out`` gives a nice natural-looking tween.

Reference
---------

.. attribute:: easings

    A dictionary mapping the names of built-in easings to the corresponding
    functions


Polynomial easing functions
...........................

.. autofunction:: linear

    .. easing_graph:: linear

.. autofunction:: quad

    .. easing_graph:: quad

.. autofunction:: cubic

    .. easing_graph:: cubic

.. autofunction:: quart

    .. easing_graph:: quart

.. autofunction:: quint

    .. easing_graph:: quint

Other simple easing functions
.............................

.. autofunction:: sine

    .. easing_graph:: sine

.. autofunction:: expo

    .. easing_graph:: expo

.. autofunction:: circ

    .. easing_graph:: circ

Parametrizable easing functions
...............................

Use keyword arguments to override the defaults.

.. autofunction:: elastic

    .. easing_graph:: elastic

.. autofunction:: back

    .. easing_graph:: back

.. autofunction:: bounce

    .. easing_graph:: bounce

.. note:: Use :func:`partial` to make easing
          functions with different parameters.

Helpers for creating new easing functions
.........................................

.. autofunction:: easing
.. autofunction:: normalized
.. autofunction:: partial


.. autofunction:: ease_out
.. autofunction:: ease_in_out
.. autofunction:: ease_out_in
.. autofunction:: ease_in
"""

import functools
import math
import inspect

tau = math.pi * 2


easings = {}


def normalized(func):
    """Decorator that normalizes an easing function

    Normalizing is done so that func(0) == 0 and func(1) == 1.

    If func(0) == func(1), ZeroDivision is raised when the result is called.
    """
    minimum = func(0)
    maximum = func(1)
    if (minimum, maximum) == (0, 1):
        return func
    range_ = maximum - minimum

    def _normalized(t, **kwargs):
        return (func(t, **kwargs) - minimum) / range_
    _wraps(_normalized, func, 'normalized')
    _normalized.__doc__ = func.__doc__

    return _normalized


def _wraps(decorated, orig, postfix):
    decorated.__signature__ = inspect.signature(orig)
    try:
        decorated.__name__ = str(orig.__name__ + '_' + postfix)
    except AttributeError:
        pass
    return decorated


def ease_out(func):
    """Given an "in" easing function, return corresponding "out" function"""
    def _ease_out(t, **kwargs):
        return 1 - func(1 - t, **kwargs)
    return _wraps(_ease_out, func, 'out')


def ease_out_in(func):
    """Given an "in" easing function, return corresponding "out-in" function"""
    def _ease_out_in(t, **kwargs):
        if t < 0.5:
            return (1 - func(1 - 2 * t, **kwargs)) / 2
        else:
            return func(2 * (t - .5), **kwargs) / 2 + .5
    return _wraps(_ease_out_in, func, 'out_in')


def ease_in_out(func):
    """Given an "in" easing function, return corresponding "in-out" function"""
    def _ease_in_out(t, **kwargs):
        if t < 0.5:
            return func(2 * t, **kwargs) / 2
        else:
            return 1 - func(1 - 2 * (t - .5), **kwargs) / 2
    return _wraps(_ease_in_out, func, 'in_out')


def ease_in(func):
    """Return :token:`func` itself. Included for symmetry."""
    return func


def easing(func):
    """Decorator for easing functions.

    Adds the :token:`in_`, :token:`out`, :token:`in_out` and :token:`out_in`
    functions to an easing function.
    """
    func.in_ = func
    func.out = ease_out(func)
    func.in_out = ease_in_out(func)
    func.out_in = ease_out_in(func)
    return func


def _easing(func):
    func = easing(func)
    easings[func.__name__] = func
    return func


@_easing
def linear(t):
    """Linear interpolation: t → t"""
    return t


@_easing
def quad(t):
    """Quadratic easing: t → t²"""
    return t * t


@_easing
def cubic(t):
    """Cubic easing: t → t³"""
    return t ** 3


@_easing
def quart(t):
    """Quartic easing: t → t⁴"""
    return t ** 4


@_easing
def quint(t):
    """Quintic easing: t → t⁵"""
    return t ** 5


@_easing
def sine(t):
    """Sinusoidal easing: Quarter of a cosine wave"""
    return 1 - math.cos(t * tau / 4)


@_easing
@normalized
def expo(t):
    """Exponential easing"""
    if t in (0, 1):
        return t
    else:
        return 2 ** (10 * (t - 1))


@_easing
def circ(t):
    """Circular easing"""
    if t >= 1:
        return 1
    return 1 - math.sqrt(1 - t * t)


@_easing
def elastic(t, *, amplitude=1, period=0.3):
    """Elastic easing"""
    if not t:
        return 0
    if t == 1:
        return 1

    if amplitude < 1:
        amplitude = 1
        s = period / 4
    else:
        s = period / tau * math.asin(1 / amplitude)

    t -= 1
    return -amplitude * 2 ** (10 * t) * math.sin((t - s) * tau / period)


@_easing
def back(t, *, amount=1.70158):
    """Overshoot easing"""
    return t * t * ((amount + 1) * t - amount)


@_easing
def bounce(t, *, amplitude=1):
    """Bouncy easing"""
    if t == 1:
        return 1
    if t < 4 / 11:
        return 7.5625 * t * t
    if t < 8 / 11:
        t -= 6 / 11
        return 1 - amplitude * (1 - (7.5625 * t * t + .75))
    if t < 10 / 11:
        t -= 9 / 11
        return 1 - amplitude * (1 - (7.5625 * t * t + .9375))
    else:
        t -= 21 / 22
        return 1 - amplitude * (1 - (7.5625 * t * t + .984375))


def partial(func, **kwargs):
    """Combines :func:`functools.partial` and :func:`easing`.

    For example, a large overshoot tween can be created as::

        >>> from gillcup import easings
        >>> large_overshoot = easings.partial(easings.back, amount=4)
        >>> large_overshoot.out(0.4)
        1.3...

    ..

        .. easing_graph:: large_overshoot

    """
    partl = functools.partial(func, **kwargs)
    partl.__name__ = '{}⟨{}⟩'.format(
        func.__name__,
        ', '.join('{}={}'.format(k, v) for k, v in kwargs.items())
    )
    return easing(partl)
