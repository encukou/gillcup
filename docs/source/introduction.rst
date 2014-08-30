Introduction
============

Gillcup is a 2D animation library.

It is intended for both scripted and interactive animations:
in the former, the entire animation is known ahead of time,
and rendered as fast as possible;
the latter is gnerally tied to a system clock,
and can be influenced by user input.

The Gillcup core is only concerned with animations;
it’s not tied to any particular graphics library.

.. todo

There should be a nice beginner-friendly top-down tutorial here.
Until that's the case, let's start with Gillcup's design.

Design
======

*   The :mod:`~gillcup.clocks` provide a customizable, discrete-time event
    system, based on futures and coroutines of Python's :mod:`asyncio` library.
*   The :mod:`~gillcup.expressions` make it possible to define and evaluate
    numeric expressions based on external factors such as Clock time.
*   The :mod:`~gillcup.properties` enable extra behavior when *expressions*
    are used as properties of objects.
*   The :mod:`~gillcup.signals` provide notifications.
*   The :mod:`~gillcup.easings` module contains tweening functions
    to spice up motion.

.. toctree::
   :hidden:

   clocks
   expressions
   properties
   signals
   easings
