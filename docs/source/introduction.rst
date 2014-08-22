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

.. automodule:: gillcup

.. toctree::
   :hidden:

   clocks
   expressions
   properties
   signals
   easings
