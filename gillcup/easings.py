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

.. autofunction:: circ

    .. easing_graph:: circ

Parametrizable easing functions
...............................

Use keyword arguments to override the defaults.

.. autofunction:: expo

    .. easing_graph:: expo

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


def _wraps(decorated, orig, postfix):
    decorated.__signature__ = inspect.signature(orig)
    if postfix:
        postfix = '_' + postfix
    else:
        postfix = ''
    try:
        decorated.__name__ = str(orig.__name__ + postfix)
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

        >>> @easing
        ... def staircase(t, *, steps=5):
        ...     return ((t * steps) // 1) / steps

    ..

        .. easing_graph:: staircase

    """
    func.in_ = func
    func.out = ease_out(func)
    func.in_out = ease_in_out(func)
    func.out_in = ease_out_in(func)
    return func


def normalized(func):
    """Decorator that normalizes an easing function

    Normalizing is done so that func(0) == 0 and func(1) == 1.


        >>> @easing
        ... @normalized
        ... def wiggly(t):
        ...     return (t + 10) ** 2 + math.cos(t * 50)

    ..

        .. easing_graph:: wiggly

    If func(0) == func(1), :exc:`ZeroDivision` is raised.

    """
    minimum = func(0)
    maximum = func(1)
    if (minimum, maximum) == (0, 1):
        return func
    scale = 1 / (maximum - minimum)

    def _normalized(t, **kwargs):
        return (func(t, **kwargs) - minimum) * scale
    _wraps(_normalized, func, None)
    _normalized.__doc__ = func.__doc__

    return _normalized


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


def _easing(func):
    func = easing(func)
    easings[func.__name__] = func
    return func


@_easing
def linear(t):
    r"""Linear interpolation

    .. math:: \mathrm{linear}(t) = t
    """
    return t


@_easing
def quad(t):
    r"""Quadratic easing

    .. math:: \mathrm{quad}(t) = t ^ 2
    """
    return t * t


@_easing
def cubic(t):
    r"""Cubic easing

    .. math:: \mathrm{cubic}(t) = t ^ 3
    """
    return t ** 3


@_easing
def quart(t):
    r"""Quartic easing

    .. math:: \mathrm{quart}(t) → t ^ 4
    """
    return t ** 4


@_easing
def quint(t):
    r"""Quintic easing

    .. math:: \mathrm{quint}(t) → t ^ 5
    """
    return t ** 5


@_easing
def sine(t):
    r"""Sinusoidal easing: Quarter of a cosine wave

    .. math:: \mathrm{sine}(t) = \cos\left(\frac{tτ}{4}\right)
    """
    return 1 - math.cos(t * tau / 4)


@_easing
@normalized
def expo(t, *, exponent=10):
    r"""Exponential easing

    .. math:: \mathrm{expo}^\prime(t, x) = 2 ^ {x (t - 1)}

    The result is normalized to the proper range using :func:`normalized`.
    """
    return 2 ** (exponent * (t - 1))


@_easing
def circ(t):
    r"""Circular easing: Quarter of a circle

    .. math:: \mathrm{circ}(t) = 1 - \sqrt{1 - t ^ 2}
    """
    if t >= 1:
        return 1
    return 1 - math.sqrt(1 - t * t)


@_easing
def elastic(t, *, amplitude=1, period=0.3):
    r"""Elastic easing

    .. math::
        \begin{aligned}
            &\mathrm{elastic}(t, a, p) = -2A ^ {10t}
                                   \sin\frac{sτ}{p} \\
            &\text{where:} \\
            &A = \begin{cases}
                    1                   & \text{if } a < 1 \\
                    a                   & \text{otherwise} \\
                \end{cases} \\
            &s = \begin{cases}
                    (t - \frac{p}{4}    & \text{if } a < 1 \\
                    (t - \frac{p}{τ} \arcsin\frac{1}{a})
                                        & \text{otherwise}  \\
                \end{cases} \\
        \end{aligned}
    """
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
    r"""Overshoot easing

    .. math:: \mathrm{back}(t, x) =
              t^2 · (t(x + 1) - x)

    The default :token:`amount` results in 10% overshoot.
    """
    return t * t * ((amount + 1) * t - amount)


@_easing
def bounce(t, *, amplitude=1):
    r"""Bouncy easing

    .. math::

        \mathrm{bounce}(t, a) = \begin{cases}
            \frac{\;11^2}{16} t^2  & \text{if } t < \frac{4}{11} \\
            1 - a \left(1 - \frac{\;11^2}{16} \left(t-\frac{6}{11}\right)^2 -
                            \frac{3}{4}\right)
                                & \text{if } t < \frac{8}{11} \\
            1 - a \left(1 - \frac{\;11^2}{16} \left(t-\frac{9}{11}\right)^2 -
                            \frac{15}{16}\right)
                                & \text{if } t < \frac{10}{11} \\
            1 - a \left(1 - \frac{\;11^2}{16} \left(t-\frac{21}{22}\right)^2 -
                            \frac{63}{64}\right)
                                & \text{if } t < 1 \\
            1                   & \text{otherwise} \\
        \end{cases}
    """
    if t < 4 / 11:
        return 121 / 16 * t * t
    if t < 8 / 11:
        t -= 6 / 11
        return 1 - amplitude * (1 - 121 / 16 * t * t - 3 / 4)
    if t < 10 / 11:
        t -= 9 / 11
        return 1 - amplitude * (1 - 121 / 16 * t * t - 15 / 16)
    elif t < 1:
        t -= 21 / 22
        return 1 - amplitude * (1 - 121 / 16 * t * t - 63 / 64)
    else:
        return 1
