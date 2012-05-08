"""Gillcup, a Python animation library

Gillcup provides a number of modules:

.. toctree::
    :maxdepth: 1

    clock
    actions
    properties
    animation
    easing

The most interesting classes of each module are exported directly
from the gillcup package:

* :class:`~gillcup.Clock` (from :mod:`gillcup.clock`)
* :class:`~gillcup.Subclock` (from :mod:`gillcup.clock`)
* :class:`~gillcup.Action` (from :mod:`gillcup.actions`)
* :class:`~gillcup.AnimatedProperty` (from :mod:`gillcup.properties`)
* :class:`~gillcup.TupleProperty` (from :mod:`gillcup.properties`)
* :class:`~gillcup.Animation` (from :mod:`gillcup.animation`)
"""

__version__ = '0.2.0-beta'
__version_info__ = (0, 2, 0, 'beta')

from gillcup.clock import Clock, Subclock
from gillcup.actions import Action
from gillcup.properties import AnimatedProperty, TupleProperty
from gillcup.animation import Animation
