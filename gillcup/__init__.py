"""Gillcup, a Python animation library

Gillcup provides a number of modules:

.. toctree::
    :maxdepth: 1

    clock
    actions
    properties
    animation
    effect
    easing

The most interesting classes of each module are exported directly
from the gillcup package:

* :class:`~gillcup.Clock` (from :mod:`gillcup.clock`)
* :class:`~gillcup.Subclock` (from :mod:`gillcup.clock`)
* :class:`~gillcup.Action` (from :mod:`gillcup.actions`)
* :class:`~gillcup.AnimatedProperty` (from :mod:`gillcup.properties`)
* :class:`~gillcup.TupleProperty` (from :mod:`gillcup.properties`)
* :class:`~gillcup.Animation` (from :mod:`gillcup.animation`)
* :class:`~gillcup.Effect` (from :mod:`gillcup.effect`)
* :class:`~gillcup.ConstantEffect` (from :mod:`gillcup.effect`)
"""

__version__ = '0.2.0-beta.2'
__version_info__ = (0, 2, 0, 'beta', 2)

from gillcup.clock import Clock, Subclock
from gillcup.actions import Action
from gillcup.properties import AnimatedProperty, TupleProperty
from gillcup.animation import Animation
from gillcup.effect import Effect, ConstantEffect
