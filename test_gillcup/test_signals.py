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

    def check(self, *expected):
        assert tuple(self.collected) == expected

    def const_collector(self, item):
        return lambda: self.collect(item)


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

    SomeClass.sig.connect(collector.const_collector('Class'), weak=False)
    instance_a.sig.connect(collector.const_collector('a'), weak=False)
    instance_b.sig.connect(collector.const_collector('b'), weak=False)

    collector.check()
    SomeClass.sig()
    collector.check('Class')
    instance_a.sig()
    collector.check('Class', 'a')
    instance_b.sig()
    collector.check('Class', 'a', 'b')
