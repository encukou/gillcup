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
