import gc

import pytest

from gillcup.signals import Signal


@pytest.fixture
def signal():
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


def test_simple_listener(signal, collector):
    assert not signal
    signal.connect(collector.collect)
    assert signal
    signal(3)
    signal(4)
    collector.check(3, 4)
    assert signal


def test_disconnect(signal, collector):
    assert not signal
    signal.connect(collector.collect)
    assert signal
    signal.disconnect(collector.collect)
    assert not signal
    signal(1)
    collector.check()


def test_weakness(signal):
    collector = Collector()
    collected = collector.collected
    assert not signal
    signal.connect(collector.collect)
    assert signal
    del collector
    gc.collect()
    signal(3)
    assert not signal
    assert collected == []


def test_strongness(signal):
    collector = Collector()
    collected = collector.collected
    assert not signal
    signal.connect(collector.collect, weak=False)
    assert signal
    del collector
    gc.collect()
    signal(3)
    assert signal
    assert collected == [3]


def test_weakness_function(signal):
    collected = []

    def collect(arg):
        collected.append(arg)
    assert not signal
    signal.connect(collect)
    assert signal
    del collect
    gc.collect()
    signal(3)
    assert not signal
    assert collected == []


def test_strongness_function(signal):
    collected = []

    def collect(arg):
        collected.append(arg)
    assert not signal
    signal.connect(collect, weak=False)
    assert signal
    del collect
    gc.collect()
    signal(3)
    assert signal
    assert collected == [3]


@pytest.mark.parametrize('weak1, weak2', [
    (True, True),
    (True, False),
    (False, True),
    (False, False),
])
def test_connection_uniqueness(signal, collector, weak1, weak2):
    signal.connect(collector.collect, weak=weak1)
    signal.connect(collector.collect, weak=weak2)
    signal(3)
    collector.check(3)


@pytest.mark.parametrize('weak1, weak2', [
    (True, True),
    (True, False),
    (False, True),
    (False, False),
])
def test_connection_uniqueness(signal, collector, weak1, weak2):
    signal.connect(collector.collect, weak=weak1)
    signal.connect(collector.collect, weak=weak2)
    signal(3)
    collector.check(3)


@pytest.mark.parametrize('weak1, weak2', [
    (True, False),
    (False, True),
    (False, False),
])
def test_strong_preference(signal, weak1, weak2):
    collector = Collector()
    signal.connect(collector.collect, weak=weak1)
    signal.connect(collector.collect, weak=weak2)
    collected = collector.collected
    del collector
    gc.collect()
    signal(3)
    assert collected == [3]


def test_simple_results(signal):
    signal.connect(lambda: 1, weak=False)
    signal.connect(lambda: 2, weak=False)
    signal.connect(lambda: 3, weak=False)
    assert sorted(signal()) == [1, 2, 3]


def test_simple_chaining(signal):
    signal2 = Signal()
    signal.connect(lambda: 1, weak=False)
    signal.connect(lambda: 2, weak=False)
    signal.connect(lambda: 3, weak=False)
    signal2.connect(lambda: 4, weak=False)
    signal2.connect(lambda: 5, weak=False)
    signal2.connect(lambda: 6, weak=False)
    signal.connect(signal2)
    assert sorted(signal()) == [1, 2, 3, 4, 5, 6]


def test_chaining_with_lists(signal):
    signal2 = Signal()
    signal.connect(lambda: [1, 2], weak=False)
    signal2.connect(lambda: [3, 4], weak=False)
    signal.connect(signal2)
    assert sorted(signal()) == [[1, 2], [3, 4]]


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
        Signal(sig=lambda instance: None)


def test_arg_adapter(signal, collector):
    signal.connect(collector.collect)
    signal.connect(collector.collect, arg_adapter=lambda *k, **a: (['y'], {}))
    signal.connect(collector.collect, arg_adapter=lambda *k, **a: (['z'], {}))

    collector.check()
    signal('x')
    collector.check_set('x', 'y', 'z')


def test_arg_adapter_disconnection(signal, collector):
    adapt_y = lambda *k, **a: (['y'], {})
    adapt_z = lambda *k, **a: (['z'], {})
    signal.connect(collector.collect)
    signal.connect(collector.collect, arg_adapter=adapt_y)
    signal.connect(collector.collect, arg_adapter=adapt_z)
    signal.connect(collector.collect, arg_adapter=adapt_z)

    collector.check()
    signal('x')
    collector.check_set('x', 'y', 'z')
    collector.clear()

    signal.disconnect(collector.collect, arg_adapter=adapt_z)
    collector.check()
    signal('x')
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
