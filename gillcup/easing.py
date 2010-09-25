#! /usr/bin/python
# Encoding: UTF-8

"""
Adapded partially from Robert Penner's Easing Equations, as they
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

from __future__ import division

import math

def normalized(func):
    """Decorator to normalize another easing function

    Normalizing is done so that f(0) == 0 and f(1) == 1.
    """
    min = func(0)
    max = func(1)
    if (min, max) == (0, 1):
        return func
    range = max - min
    def normalized(t):
        return min + func(t) / range
    try:
        normalized.__name__ = func.__name__ + '_normalized'
    except AttributeError:
        pass
    return normalized

def _add_postfix(decorated, func, postfix):
    try:
        decorated.__name__ = func.__name__ + '_' + postfix
    except AttributeError:
        pass

def easeIn(func):
    return func

def easeOut(func):
    def ease_out(t):
        return 1 - func(1 - t)
    _add_postfix(ease_out, func, 'out')
    return ease_out

def easeOutIn(func):
    def ease_outIn(t):
        if t < 0.5:
            return (1 - func(1 - 2 * t)) / 2
        else:
            return func(2 * (t - .5)) / 2 + .5
    _add_postfix(ease_outIn, func, 'outIn')
    return ease_outIn

def easeInOut(func):
    def ease_outIn(t):
        if t < 0.5:
            return func(2 * t) / 2
        else:
            return 1 - func(1 - 2 * (t - .5)) / 2
    _add_postfix(ease_outIn, func, 'outIn')
    return ease_outIn

def tweenfunc(func):
    func.in_ = easeIn(func)
    func.out = easeOut(func)
    func.inOut = easeInOut(func)
    func.outIn = easeOutIn(func)
    return func

@tweenfunc
def linear(t):
    """Linear interpolation

    t → t
    """
    return t

@tweenfunc
def quad(t):
    """Quadratic easing

    t → t**2
    """
    return t ** 2

@tweenfunc
def cubic(t):
    """Cubic easing

    t → t**3
    """
    return t ** 3

@tweenfunc
def quart(t):
    """Quartic easing

    t → t**4
    """
    return t ** 4

@tweenfunc
def quint(t):
    """Quintic easing

    t → t**5
    """
    return t ** 5

@tweenfunc
def sin(t):
    """Sinusoidal easing

    Quarter of a cosine wave
    """
    return (-math.cos(t / 2 * math.pi) + 1)

@tweenfunc
def exp(t):
    """Exponential easing
    """
    if t in (0, 1):
        return t
    else:
        return 2.0 ** (10 * (t - 1)) - 0.001

@tweenfunc
def circ(t):
    """Circular easing
    """
    try:
        return 1 - math.sqrt(1 - t * t)
    except ValueError:
        return 0

def elastic(period, amplitude=1):
    """Elastic easing
    """
    @tweenfunc
    def elastic(t):
        return exp(t) * math.cos((1 - t) * 2 * math.pi / period) * amplitude
    return elastic

def overshoot(amount):
    """Overshoot easing
    """
    @tweenfunc
    def overshoot(t):
        t = 1 - t
        return 1 - t * t * ((amount + 1) * t - amount)
    return overshoot

def _bounce_helper(t, c, a):
    if t == 1:
        return c
    if t < 4 / 11:
        return c * (7.5625 * t * t)
    elif t < 8 / 11:
        t -= 6 / 11.0
        return -a * (1. - (7.5625 * t * t + .75)) + c
    elif t < 10 / 11:
        t -= 9 / 11
        return -a * (1. - (7.5625 * t * t + .9375)) + c
    else:
        t -= 21 / 22
        return -a * (1. - (7.5625 * t * t + .984375)) + c

def bounce(amplitude):
    """Bounce easing
    """
    @tweenfunc
    def bounce(t):
        return _bounce_helper(t, 1, amplitude)
    return bounce


# Execute the file for a gallery of easing funcs (matplotlib must be installed)

elastic_example = elastic(.15)
overshoot_example = overshoot(1)
bounce_example = bounce(1)

def showcase(
        items='(poly) sin exp circ elastic_example overshoot_example '
        'bounce_example'.split()
    ):
    """Show graphs of the easing functions in this module
    """
    import pylab

    time = pylab.arange(0.0, 1.01, 0.01)
    for i, n in enumerate(items):
        if n == '(poly)':
            funcs = 'linear quad cubic quart quint'.split()
        else:
            funcs = [n]
        for j, a in enumerate((easeIn, easeOut, easeInOut, easeOutIn)):
            pylab.subplot(len(items), 4, i * 4 + 1 + j)
            for funcname in funcs:
                func = a(globals()[funcname])
                s = [func(t) for t in time]
                pylab.plot(time, s, linewidth=1.0)
                if i == 0:
                    pylab.title(a.__name__)
                if j == 0:
                    title, sep, end = n.partition('_example')
                    pylab.ylabel(title)
    pylab.show()

if __name__ == '__main__':
    showcase()
