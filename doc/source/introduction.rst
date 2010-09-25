Introduction
============

Gillcup is a 2D animation library.

It is intended for both scripted (i.e. the entire animation is
known ahead of time), and interactive animations.

Gillcup is modular: the core provides a timer and animated objects with nothing
relating to graphics. Visualization classes based on Pyglet are provided in the
:py:mod:`gillcup.graphics` module.

Gillcup depends on nothing but Pyglet_, easing
deployment. Pyglet, in turn, depends on Python and OpenGL.


.. _Pyglet: http://pyglet.org/
