"""Signalling primitives

A Gillcup signal can have many receiver functions attached to it.
When the signal is called, the receivers are called as well.

The receivers are called synchronously, so they should return quickly.
Long-running work should be scheduled.

Normally, receivers are only weakly referenced, so listening to a signal
is not enough to keep an object alive.
For bound methods, :class:`weakref.WeakMethod` is used, so it's enough
that the object stays alive[#weakmeth]_.

A single receiver can not be connected to a signal multiple times.

A signal is truthy if any listeners are connected.

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

import inspect
import weakref


def _hashable_identity(obj):
    # Adapted from the Blinker project
    if inspect.ismethod(obj):
        return (id(obj.__func__), id(obj.__self__))
    else:
        return id(obj)


def _ref(obj, callback=None):
    hashable_id = _hashable_identity(obj)
    if inspect.ismethod(obj):
        ref = weakref.WeakMethod(obj, callback)
    else:
        ref = weakref.ref(obj, callback)
    return hashable_id, ref


def _dict_discard(dct, key):
    try:
        del dct[key]
    except KeyError:
        return False
    return True


class Signal:
    """A broadcasting device.

    .. automethod:: connect
    .. autospecialmethod:: __call__
    .. automethod:: disconnect
    .. autospecialmethod:: __bool__
    """

    def __init__(self):
        self._weak_receivers = {}
        self._strong_receivers = {}

        for hashable_id, ref in list(self._weak_receivers.items()):
            if not ref:
                del self._weak_receivers[hashable_id]

    def connect(self, receiver, weak=True):
        """Add the given receiver to this signal's list"""
        if weak:
            def discard(ref):
                _dict_discard(self._weak_receivers, hashable_id)
            hashable_id, ref = _ref(receiver, discard)
            self._weak_receivers.setdefault(hashable_id, ref)
        else:
            hashable_id = _hashable_identity(receiver)
            self._strong_receivers.setdefault(hashable_id, receiver)

    def disconnect(self, receiver):
        """Remove the given receiver from this signal's list"""
        hashable_id = _hashable_identity(receiver)
        if _dict_discard(self._weak_receivers, hashable_id):
            return
        if _dict_discard(self._strong_receivers, hashable_id):
            return
        raise LookupError(receiver)

    def __call__(self, *args, **kwargs):
        """Call all of this signal's receivers with the given arguments
        """
        for receiver in self._listeners:
            receiver(*args, **kwargs)

    def __bool__(self):
        """True if any listeners are connected

        Note that this only does an optimistic check;
        weak listeners may still be counted some time after they are deleted.
        """
        return bool(self._weak_receivers or self._strong_receivers)

    @property
    def _listeners(self):
        for ref in list(self._weak_receivers.values()):
            receiver = ref()
            if receiver:
                yield receiver
        yield from list(self._strong_receivers.values())
