gillcup.animation
==================

.. module:: gillcup.animation

Animations are :mod:`Actions <gillcup.actions>` that modify
:mod:`animated properties <gillcup.properties>`.
To use one, create it and schedule it on a Clock.
Once an animation is in effect, it will smoothly change a property's value
over a specified time interval.

The value is computed as a tween between the property's original value and
the Animation's **target** value.
The tween parameters can be set by the **timing** and **easing** keyword
arguments.

An animation's **target** is an :class:`~gillcup.AnimatedProperty` itself.
Also, the “original value” of a property is not fixed: it is whatever the
value would have been if this animation wasn't applied.
Animating these allows one to create very complex effects in a modular way.

.. autoclass:: gillcup.Animation

.. autoclass:: gillcup.animation.Add
.. autoclass:: gillcup.animation.Multiply
.. autoclass:: gillcup.animation.Computed
