#! /usr/bin/python
# Encoding: UTF-8

"""
Adapded roughly and partially from Robert Penner's Easing Equations, as they
appear in the Qt library. The original license follows:

TERMS OF USE - EASING EQUATIONS

Open source under the BSD License.

Copyright © 2001 Robert Penner

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

   * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.
   * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.
   * Neither the name of the author nor the names of contributors may be
     used to endorse or promote products derived from this software without
     specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

from __future__ import unicode_literals, division, print_function

import sys
import functools
import math


def normalized(func):
    """Decorator that normalizes an easing function

    Normalizing is done so that func(0) == 0 and func(1) == 1.
    """
    minimum = func(0)
    maximum = func(1)
    if (minimum, maximum) == (0, 1):
        return func
    range_ = maximum - minimum

    @functools.wraps(func)
    def _normalized(t):
        return (func(t) - minimum) / range_
    _add_postfix(_normalized, func, 'normalized')

    return _normalized


def _add_postfix(decorated, func, postfix):
    try:
        decorated.__name__ = str(func.__name__ + '_' + postfix)
    except AttributeError:  # pragma: no cover
        pass


def ease_out(func):
    """Given an "in" easing function, return corresponding "out" function"""
    def _ease_out(t):
        return 1 - func(1 - t)
    _add_postfix(_ease_out, func, 'out')
    return _ease_out


def ease_out_in(func):
    """Given an "in" easing function, return corresponding "out-in" function"""
    def _ease_out_in(t):
        if t < 0.5:
            return (1 - func(1 - 2 * t)) / 2
        else:
            return func(2 * (t - .5)) / 2 + .5
    _add_postfix(_ease_out_in, func, 'out_in')
    return _ease_out_in


def ease_in_out(func):
    """Given an "in" easing function, return corresponding "in-out" function"""
    def _ease_in_out(t):
        if t < 0.5:
            return func(2 * t) / 2
        else:
            return 1 - func(1 - 2 * (t - .5)) / 2
    _add_postfix(_ease_in_out, func, 'in_out')
    return _ease_in_out


def ease_in(func):
    """Return ``func`` itself. Included for symmetry."""
    return func


def easefunc(func):
    """Decorator for easing functions.

    Adds the **in_**, **out**, **in_out** and **out_in** attributes to
    an easing function.
    """
    func.in_ = ease_in(func)
    func.out = ease_out(func)
    func.in_out = ease_in_out(func)
    func.out_in = ease_out_in(func)
    return func


@easefunc
def linear(t):
    """Linear interpolation

    t → t
    """
    return t


@easefunc
def quadratic(t):
    """Quadratic easing

    t → t**2
    """
    return t ** 2


@easefunc
def cubic(t):
    """Cubic easing

    t → t**3
    """
    return t ** 3


@easefunc
def quartic(t):
    """Quartic easing

    t → t**4
    """
    return t ** 4


@easefunc
def quintic(t):
    """Quintic easing

    t → t**5
    """
    return t ** 5


@easefunc
def sine(t):
    """Sinusoidal easing

    Quarter of a cosine wave
    """
    return (-math.cos(t / 2 * math.pi) + 1)


@easefunc
def exponential(t):
    """Exponential easing
    """
    if t in (0, 1):
        return t
    else:
        return 2.0 ** (10 * (t - 1)) - 0.001


@easefunc
def circular(t):
    """Circular easing
    """
    try:
        return 1 - math.sqrt(1 - t * t)
    except ValueError:
        return 1


def elastic(period, amplitude=1):
    """Elastic easing factory
    """
    @easefunc
    def _elastic(t):
        b = exponential(t) * math.cos((1 - t) * 2 * math.pi / period)
        return b * amplitude
    return _elastic


def overshoot(amount):
    """Overshoot easing factory
    """
    @easefunc
    def _overshoot(t):
        return t * t * ((amount + 1) * t - amount)
    return _overshoot


def _bounce_helper(t, c, a):
    t = 1 - t
    if t == 1:
        return 1 - c
    if t < 4 / 11:
        return 1 - c * (7.5625 * t * t)
    elif t < 8 / 11:
        t -= 6 / 11.0
        return 1 + a * (1. - (7.5625 * t * t + .75)) - c
    elif t < 10 / 11:
        t -= 9 / 11
        return 1 + a * (1. - (7.5625 * t * t + .9375)) - c
    else:
        t -= 21 / 22
        return 1 + a * (1. - (7.5625 * t * t + .984375)) - c


def bounce(amplitude):
    """Bounce easing factory
    """
    @easefunc
    def _bounce(t):
        return _bounce_helper(t, 1, amplitude)
    return _bounce


# Execute the file for a gallery of easing funcs (matplotlib must be installed)

elastic_example = elastic(.15)
overshoot_example = overshoot(1)
bounce_example = bounce(1)


def showcase(
        items='(poly) sine exponential circular elastic_example '
        'overshoot_example bounce_example'.split(),
        filename=None,
    ):  # pragma: no cover; pylint: disable=R0914, W0621, W0404, F0401
    """Show graphs of the easing functions in this module
    """
    import pylab
    from matplotlib import pyplot
    from matplotlib.ticker import MultipleLocator

    pyplot.figure(figsize=(7, 7))
    pyplot.subplots_adjust(wspace=0.3, hspace=0.7)

    time = pylab.arange(0.0, 1.01, 0.01)
    for i, n in enumerate(items):
        if n == '(poly)':
            funcs = 'linear quadratic cubic quartic quintic'.split()
        else:
            funcs = [n]
        for j, a in enumerate('in_ out in_out out_in'.split()):
            ax = pylab.subplot(len(items), 4, i * 4 + 1 + j)
            ax.xaxis.set_major_locator(MultipleLocator(1))
            ax.yaxis.set_major_locator(MultipleLocator(1))
            for funcname in funcs:
                func = getattr(globals()[funcname], a)
                s = [func(t) for t in time]
                pylab.plot(time, s, linewidth=1.0)
                if i == 0:
                    pylab.title('.' + a)
                if j == 0:
                    title, sep, _end = n.partition('_example')
                    pylab.ylabel(title)
    if filename:
        pylab.savefig(filename, transparent=True)
    else:
        pylab.show()


if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = None
    showcase(filename=filename)
