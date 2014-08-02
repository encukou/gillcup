"""Signalling primitives

.. TODO:
    A Gillcup signal can have many receiver functions attached to it.
    When the signal is called, the receivers are called as well.

.. TODO:
    Normally, receivers are only weakly referenced, so listening to a signal
    is not enough to keep an object alive.
    For bound methods, :class:`weakref.WeakMethod` is used, so it's enough
    that the object stays alive[#weakmeth]_.

.. TODO:
    Receivers can return values, which are collected in a list and returned
    on signal call.

.. TODO:
    Since signals are callable, a signal can act as a receiver, so long chains
    for relaying a message can be constructed.
    Gillcup tries not to needlessly call signals that have no receivers.

.. TODO:
    Signals can be chained using an "argument adapter" function,
    which can munge arguments to adapt them to the chained signal.
    This is more efficient than using a lambda, sinceGillcup can eliminate
    calls to unconnected signals.


.. TODO:
    When a signal is added to an class, each instance of that class gets
    its own instance of the signal.

    The instance's signal calls the class signal with an extra
    "instance" keyword argument added.

.. rubric:: footnotes

.. [#weakmeth] Technically, the function wrapped by the method
               also has to stay alive.

"""
