gillcup.properties
==================

.. module:: gillcup.properties

To animate Python objects, we need to change values of their attributes over
time.
There are two kinds of changes we can make: *discrete* and *continuous*.
A discrete change happens at a single point in time: for example, an object
is shown, some output is written, a sound starts playing.
:mod:`Actions <gillcup.actions>` are used for effecting
discrete changes.

Continuous changes happen over a period of time: an object smoothly moves
to the left, or a sound fades out.
These changes are made by animating special properties on objects.

Animated properties use Python's `descriptor interface
<http://docs.python.org/howto/descriptor.html>`_ to provide efficient access to
animated properties.

Assigment to an animated attribute causes the property to get set to the given
value and cancels any running animations on it.

See :mod:`gillcup.animation` for information on how to actually do animations.

.. autoclass:: gillcup.AnimatedProperty

    .. automethod:: gillcup.AnimatedProperty.adjust_value
    .. automethod:: gillcup.AnimatedProperty.map

.. autoclass:: gillcup.TupleProperty

    .. automethod:: gillcup.TupleProperty.adjust_value
    .. automethod:: gillcup.TupleProperty.map

.. autoclass:: gillcup.properties.ScaleProperty

    .. automethod:: gillcup.properties.ScaleProperty.adjust_value

.. autoclass:: gillcup.properties.VectorProperty

    .. automethod:: gillcup.properties.VectorProperty.adjust_value
