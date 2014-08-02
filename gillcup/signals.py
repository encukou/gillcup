"""Signalling primitives

A Gillcup signal can have many listener functions attached to it.
When the signal is called, the listeners are called as well.

The listeners are called synchronously, so they should return quickly.
Long-running work should be scheduled.

Normally, listeners are only weakly referenced, so listening to a signal
is not enough to keep an object alive.
For bound methods, :class:`weakref.WeakMethod` is used, so it's enough
that the object stays alive[#weakmeth]_.

A single listener can only be connected to one signal at a time.
Strongly-referenced listeners are preferred (i.e. if both a weak listener and
a strong one are connected, only the strong reference is kept).

A signal is truthy if any listeners are connected.

Listeners can return values, which are collected in a list and returned
from the signal call.
If a signal is reistered as a listener, the results returned from it
are merged into the resulting list: the caller receives a flattened list
of all individual replies.
(If a non-signal listener returns a list, it will be inserted to the result
as is.)

.. TODO:
    Long signal chains can be constructed,
    where a signal listening on another signal,
    which is in turn listening on a thirs signal, etc.
    Gillcup tries not to needlessly call signals that have no listeners.

Signals can be chained using an "argument adapter" function,
which can munge arguments to adapt them to the chained signal.

.. TODO:
    This is more efficient than using a lambda, sinceGillcup can eliminate
    calls to unconnected signals.

When a signal is added to an class, each instance of that class will
automatically get its own instance of the signal.

.. TODO:
    The instance's signal automatically calls the class signal with an extra
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
import collections


def _hashable_identity(obj):
    # Adapted from the Blinker project
    if inspect.ismethod(obj):
        return (id(obj.__func__), id(obj.__self__))
    else:
        return id(obj)


def _ref(obj, callback=None):
    if inspect.ismethod(obj):
        return weakref.WeakMethod(obj, callback)
    else:
        return weakref.ref(obj, callback)


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
    _is_gillcup_signal = True

    def __init__(self):
        self._weak_listeners = {}
        self._strong_listeners = {}
        self._instance_signals = weakref.WeakKeyDictionary()

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        else:
            try:
                return self._instance_signals[instance]
            except KeyError:
                new_signal = type(self)()
                self._instance_signals[instance] = new_signal
                return new_signal

    def connect(self, listener, *, weak=True, arg_adapter=None):
        """Add the given listener to this signal's list

        :param listener: The new listener to add
        :param weak: If true, only a weak reference to the listener is kept
                     (via :class:`weakref.WeakMethod` for methods,
                     :class:`weakref.ref` for any other objects).
        :param arg_adapter: An optional function for transforming arguments
                            before calling the listener.
                            It will be called with the given (*args, **kwargs),
                            and must return a new (args, kwargs) tuple.
                            If None, the original arguments are used.
        """
        hashable_id = _hashable_identity(listener)
        key = hashable_id, arg_adapter

        def discard_the_weak(ref=None):
            _dict_discard(self._weak_listeners, key)
        if weak:
            if key in self._strong_listeners:
                return
            ref = _ref(listener, discard_the_weak)
            self._weak_listeners.setdefault(key, ref)
        else:
            discard_the_weak()
            self._strong_listeners.setdefault(key, listener)

    def disconnect(self, listener, *, arg_adapter=None):
        """Remove the given listener from this signal's list

        Raises :class:`LookupError` if the listener is not found.

        Both the :token:`listener` and :token:`arg_adapter` must match
        values given in an earlier call to :meth:`connect`.
        """
        key = (_hashable_identity(listener), arg_adapter)
        if _dict_discard(self._weak_listeners, key):
            return
        if _dict_discard(self._strong_listeners, key):
            return
        raise LookupError(listener)

    def __call__(self, *args, **kwargs):
        """Call all of this signal's listeners with the given arguments
        """
        result = []
        for (_h, arg_adapter), listener in self._listeners:
            if arg_adapter is None:
                partial_result = listener(*args, **kwargs)
            else:
                new_args, new_kwargs = arg_adapter(*args, **kwargs)
                partial_result = listener(*new_args, **new_kwargs)
            if getattr(listener, '_is_gillcup_signal', None):
                result.extend(partial_result)
            else:
                result.append(partial_result)
        return result

    def __bool__(self):
        """True if any listeners are connected

        Note that this only does an optimistic check;
        weak listeners may still be counted some time after they are deleted.
        """
        return bool(self._weak_listeners or self._strong_listeners)

    @property
    def _listeners(self):
        weaklings = list(self._weak_listeners.items())
        stronglings = list(self._strong_listeners.items())
        for key, listener in weaklings:
            listener = listener()
            if listener:
                yield key, listener
        yield from stronglings