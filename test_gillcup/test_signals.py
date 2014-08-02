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


@pytest.fixture
def collector():
    return Collector()


def test_simple_callback(signal, collector):
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
