import gc
import inspect

import pytest

from gillcup.signals import Signal, signal


@pytest.fixture
def sig():
    return Signal()


class Collector:
    def __init__(self):
        self.collected = []

    def collect(self, item):
        self.collected.append(item)

    def clear(self):
        self.collected.clear()

    def check(self, *expected):
        assert tuple(self.collected) == expected

    def check_set(self, *expected):
        assert set(self.collected) == set(expected)
        assert len(self.collected) == len(expected)

    def const_collector(self, item):
        return lambda: self.collect(item)

    def kwarg_collector(self, name):
        return lambda **kwargs: self.collect(kwargs[name])

@pytest.fixture
def collector():
    return Collector()


def test_simple_listener(sig, collector):
    assert not sig
    sig.connect(collector.collect)
    assert sig
    sig(3)
    sig(4)
    collector.check(3, 4)
    assert sig


def test_disconnect(sig, collector):
    assert not sig
    sig.connect(collector.collect)
    assert sig
    sig.disconnect(collector.collect)
    assert not sig
    sig(1)
    collector.check()


def test_weakness(sig):
    collector = Collector()
    collected = collector.collected
    assert not sig
    sig.connect(collector.collect, weak=True)
    assert sig
    del collector
    gc.collect()
    sig(3)
    assert not sig
    assert collected == []


def test_strongness(sig):
    collector = Collector()
    collected = collector.collected
    assert not sig
    sig.connect(collector.collect, weak=False)
    assert sig
    del collector
    gc.collect()
    sig(3)
    assert sig
    assert collected == [3]


def test_weakness_function(sig):
    collected = []

    def collect(arg):
        collected.append(arg)
    assert not sig
    sig.connect(collect, weak=True)
    assert sig
    del collect
    gc.collect()
    sig(3)
    assert not sig
    assert collected == []


def test_strongness_function(sig):
    collected = []

    def collect(arg):
        collected.append(arg)
    assert not sig
    sig.connect(collect, weak=False)
    assert sig
    del collect
    gc.collect()
    sig(3)
    assert sig
    assert collected == [3]


@pytest.mark.parametrize('weak1, weak2', [
    (True, True),
    (True, False),
    (False, True),
    (False, False),
])
def test_connection_uniqueness(sig, collector, weak1, weak2):
    sig.connect(collector.collect, weak=weak1)
    sig.connect(collector.collect, weak=weak2)
    sig(3)
    collector.check(3)


@pytest.mark.parametrize('weak1, weak2', [
    (True, True),
    (True, False),
    (False, True),
    (False, False),
])
def test_connection_uniqueness(sig, collector, weak1, weak2):
    sig.connect(collector.collect, weak=weak1)
    sig.connect(collector.collect, weak=weak2)
    sig(3)
    collector.check(3)


@pytest.mark.parametrize('weak1, weak2', [
    (True, False),
    (False, True),
    (False, False),
])
def test_strong_preference(sig, weak1, weak2):
    collector = Collector()
    sig.connect(collector.collect, weak=weak1)
    sig.connect(collector.collect, weak=weak2)
    collected = collector.collected
    del collector
    gc.collect()
    sig(3)
    assert collected == [3]


def test_simple_results(sig):
    sig.connect(lambda: 1, weak=False)
    sig.connect(lambda: 2, weak=False)
    sig.connect(lambda: 3, weak=False)
    assert sorted(sig()) == [1, 2, 3]


def test_simple_chaining(sig):
    signal2 = Signal()
    sig.connect(lambda: 1, weak=False)
    sig.connect(lambda: 2, weak=False)
    sig.connect(lambda: 3, weak=False)
    signal2.connect(lambda: 4, weak=False)
    signal2.connect(lambda: 5, weak=False)
    signal2.connect(lambda: 6, weak=False)
    sig.connect(signal2)
    assert sorted(sig()) == [1, 2, 3, 4, 5, 6]


def test_chaining_with_lists(sig):
    signal2 = Signal()
    sig.connect(lambda: [1, 2], weak=False)
    signal2.connect(lambda: [3, 4], weak=False)
    sig.connect(signal2)
    assert sorted(sig()) == [[1, 2], [3, 4]]


def test_instance_signals(collector):

    class SomeClass:
        sig = Signal()

    instance_a = SomeClass()
    instance_b = SomeClass()

    SomeClass.sig.connect(collector.kwarg_collector('instance'), weak=False)
    instance_a.sig.connect(collector.const_collector('a'), weak=False)
    instance_b.sig.connect(collector.const_collector('b'), weak=False)

    collector.check()
    SomeClass.sig(instance=None)
    collector.check(None)
    instance_a.sig()
    collector.check_set(None, 'a', instance_a)
    instance_b.sig()
    collector.check_set(None, 'a', instance_a, 'b', instance_b)


def test_instance_signals_only(collector):

    class SomeClass:
        sig = Signal()

    instance_a = SomeClass()
    instance_b = SomeClass()

    instance_a.sig.connect(collector.const_collector('a'), weak=False)
    instance_b.sig.connect(collector.const_collector('b'), weak=False)

    collector.check()
    SomeClass.sig()
    collector.check()
    instance_a.sig()
    collector.check('a')
    instance_b.sig()
    collector.check('a', 'b')


def test_reserved_param_name(collector):
    with pytest.raises(ValueError) as e:
        Signal(signature=inspect.signature(lambda instance: None))


def test_arg_adapter(sig, collector):
    sig.connect(collector.collect)
    sig.connect(collector.collect, arg_adapter=lambda *k, **a: (['y'], {}))
    sig.connect(collector.collect, arg_adapter=lambda *k, **a: (['z'], {}))

    collector.check()
    sig('x')
    collector.check_set('x', 'y', 'z')


def test_arg_adapter_disconnection(sig, collector):
    adapt_y = lambda *k, **a: (['y'], {})
    adapt_z = lambda *k, **a: (['z'], {})
    sig.connect(collector.collect)
    sig.connect(collector.collect, arg_adapter=adapt_y)
    sig.connect(collector.collect, arg_adapter=adapt_z)
    sig.connect(collector.collect, arg_adapter=adapt_z)

    collector.check()
    sig('x')
    collector.check_set('x', 'y', 'z')
    collector.clear()

    sig.disconnect(collector.collect, arg_adapter=adapt_z)
    collector.check()
    sig('x')
    collector.check_set('x', 'y')


def test_lazy_connect(collector):
    s1 = Signal()
    s2 = Signal()
    s3 = Signal()

    s1.connect(s2)
    s2.connect(s3)

    assert not s1
    assert not s2
    assert not s3

    s3.connect(collector.collect)

    assert s1
    assert s2
    assert s3

    s1(3)
    collector.check(3)


def test_naming__none():
    sig = Signal()
    assert sig.name == None
    assert sig.__doc__ == 'A signal'


def test_naming__name():
    sig = Signal('changed')
    assert sig.name == 'changed'
    assert sig.__doc__ == "Signal 'changed'"


def test_naming__both():
    sig = Signal('changed', doc='Notify of any change')
    assert sig.name == 'changed'
    assert sig.__doc__ == 'Notify of any change'


def test_naming__doc():
    sig = Signal(doc='Notify of any change')
    assert sig.name == None
    assert sig.__doc__ == 'Notify of any change'


def test_decorator():

    @signal
    def value_changed(old_value, new_value):
        """Notifies of a value change"""

    assert value_changed.name == 'value_changed'
    assert list(value_changed.signature.parameters) == [
        'old_value', 'new_value']
    assert value_changed.__doc__ == 'Notifies of a value change'
    assert repr(value_changed) == (
        '<Signal value_changed(old_value, new_value)>')


def test_decorator_on_class():
    class Foo:
        @signal
        def value_changed(old_value, new_value):
            """Notifies of a value change"""

    assert Foo.value_changed.name == 'value_changed'
    assert list(Foo.value_changed.signature.parameters) == [
        'old_value', 'new_value', 'instance']
    assert Foo.value_changed.__doc__ == 'Notifies of a value change'
    assert repr(Foo.value_changed) == (
        '<Signal value_changed(old_value, new_value, *, instance=None) '
        'of {owner!r}>'.format(owner=Foo))


def test_decorator_on_instance():
    class Foo:
        @signal
        def value_changed(old_value, new_value):
            """Notifies of a value change"""
    foo = Foo()

    assert foo.value_changed.name == 'value_changed'
    assert list(foo.value_changed.signature.parameters) == [
        'old_value', 'new_value']
    assert foo.value_changed.__doc__ == 'Notifies of a value change'
    assert repr(foo.value_changed) == (
        '<Signal value_changed(old_value, new_value) '
        'of {owner!r}>'.format(owner=foo))


def test_signature_checking():

    @signal
    def value_changed(old_value, new_value):
        """Notifies of a value change"""

    value_changed(1, 2)
    value_changed(old_value=1, new_value=2)

    with pytest.raises(TypeError):
        value_changed()

    with pytest.raises(TypeError):
        value_changed(1, 2, foo=5)


def test_no_weak_builtin_method(sig):
    with pytest.raises(TypeError):
        sig.connect([].append, weak=True)


def test_default_strong_lambda(sig):
    lst = []
    sig.connect(lambda x: lst.append(x))
    gc.collect()
    sig(3)
    assert lst == [3]


def test_default_strong_builtin_method(sig):
    lst = []
    sig.connect(lst.append)
    gc.collect()
    sig(3)
    assert lst == [3]


def test_default_weak_method(sig):
    collector = Collector()
    collected = collector.collected
    sig.connect(collector.collect)
    del collector
    gc.collect()
    sig(3)
    assert collected == []
