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

Long signal chains can be constructed,
where a signal is listening on another signal,
which is in turn listening on a third signal, etc.
Gillcup tries not to needlessly call signals that have no listeners.

Signals can be chained using an "argument adapter" function,
which can munge arguments to adapt them to the chained signal.
(This is more efficient than using a lambda, since Gillcup can eliminate
calls to unconnected signals.)

When a signal is added to an class, each instance of that class will
automatically get its own instance of the signal.
The instance's signal automatically calls the class signal with an "instance"
keyword argument added.
This argument is added to the signature of class-bound signals,
and cannot be used for other purposes.

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

from gillcup import util


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


def _instance_arg_adapter(instance):
    def func(*args, **kwargs):
        kwargs['instance'] = instance
        return args, kwargs
    return func


class Signal:
    """A broadcasting device.

    :param name: Optional name of the signal.
                Available as :token:`name` attribute
    :param doc: Optional documentation for the signal.
                Available as the docstring.
    :param sig: Optional signature for the signal.
                Available as the docstring.

                If a callable is given, the signature is extracted from it,
                i.e., you can give an example receiver to :token:`sig`.

    Methods:

        .. automethod:: connect
        .. autospecialmethod:: __call__
        .. automethod:: disconnect
        .. autospecialmethod:: __bool__
    """
    _is_gillcup_signal = True

    @util.fix_public_signature
    def __init__(self, name=None, *, doc=None, sig=None, _internal=False):
        self._weak_listeners = {}
        self._strong_listeners = {}
        self._instance_signals = weakref.WeakKeyDictionary()
        self._waiting_connections = []

        self.name = name

        if not sig:
            sig = self.__call__
        if callable(sig):
            sig = inspect.signature(sig)
        if not _internal and 'instance' in sig.parameters:
            raise ValueError(
                'The parameter name "instance" is reserved by gillcup')
        self.sig = self.__signature__ = sig

        if doc:
            self.__doc__ = doc
        elif name:
            self.__doc__ = "Signal '%s'" % name
        else:
            self.__doc__ = 'A signal'

    def __get__(self, instance, owner=None):
        parent = None
        if instance is None:
            key = owner
            extra_arg = inspect.Parameter(
                name='instance',
                kind=inspect.Parameter.KEYWORD_ONLY)

            def _params_gen():
                existing = iter(self.sig.parameters.values())
                for param in existing:
                    if param.kind in (inspect.Parameter.KEYWORD_ONLY,
                                      inspect.Parameter.VAR_KEYWORD):
                        yield extra_arg
                        yield param
                        break
                    else:
                        yield param
                else:
                    yield extra_arg
                yield from existing
            sig = self.sig.replace(parameters=list(_params_gen()))
        else:
            key = instance
            sig = self.sig
            if owner:
                parent = self.__get__(None, owner)
        try:
            return self._instance_signals[key]
        except KeyError:
            new_signal = type(self)(self.name, doc=self.__doc__,
                                    sig=self, _internal=True)
            if parent:
                new_signal.connect(parent,
                                   arg_adapter=_instance_arg_adapter(instance))
            self._instance_signals[key] = new_signal
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
        try:
            connect_override = listener._gillcup_signal_connect_override
        except AttributeError:
            pass
        else:
            if connect_override(self, weak, arg_adapter):
                return
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
        for signal, weak, arg_adapter in self._waiting_connections:
            signal.connect(self, weak=weak, arg_adapter=arg_adapter)

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
        self.sig.bind(*args, **kwargs)
        result = []
        for (_h, arg_adapter), listener in self._listeners:
            is_signal = getattr(listener, '_is_gillcup_signal', None)
            if is_signal and not listener:
                # TODO: Disconnect & go back to _waiting_connections?
                continue
            if arg_adapter is None:
                partial_result = listener(*args, **kwargs)
            else:
                new_args, new_kwargs = arg_adapter(*args, **kwargs)
                partial_result = listener(*new_args, **new_kwargs)
            if is_signal:
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

    def _gillcup_signal_connect_override(self, signal, weak, arg_adapter):
        if self:
            return False
        else:
            self._waiting_connections.append((signal, weak, arg_adapter))
            return True

    @property
    def _listeners(self):
        weaklings = list(self._weak_listeners.items())
        stronglings = list(self._strong_listeners.items())
        for key, listener in weaklings:
            listener = listener()
            if listener:
                yield key, listener
        yield from stronglings
