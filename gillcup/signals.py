"""Signalling primitives

A Gillcup signal can have many receiver functions attached to it.
When the signal is called, the receivers are called as well.

A signal is truthy if it has any listeners attached to it.

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

Reference
---------

.. autoclass:: Signal

"""


class Signal:
    """A broadcasting device.

    .. automethod:: connect
    .. autospecialmethod:: __call__
    .. automethod:: disconnect
    .. autospecialmethod:: __bool__
    """

    def __init__(self):
        self._listeners = []

    def connect(self, listener):
        """Add the given receiver to this signal's list"""
        self._listeners.append(listener)

    def disconnect(self, listener):
        """Remove the given receiver from this signal's list"""
        self._listeners.remove(listener)

    def __call__(self, *args, **kwargs):
        """Call all of this signal's receivers with the given arguments"""
        for listener in self._listeners:
            listener(*args, **kwargs)

    def __bool__(self):
        """True if any listeners are connected"""
        return bool(self._listeners)
