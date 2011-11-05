from __future__ import division

import pytest

from gillcup import Clock

def dummy_function():
    pass

def append_const(lst, value):
    def append():
        lst.append(value)
    return append

def append_time(lst, clock):
    def append():
        lst.append(clock.time)
    return append

def test_clock():
    clock = Clock()
    assert clock.time == 0
    clock.advance(1)
    assert clock.time == 1

def test_scheduling():
    clock = Clock()
    lst = []
    clock.schedule(append_const(lst, 'a'), 1)
    clock.schedule(append_const(lst, 'd'), 3)
    clock.schedule(append_const(lst, 'b'), 1)
    clock.schedule(append_const(lst, 'c'), 1)
    clock.advance(0)
    assert lst == []
    clock.advance(1)
    assert lst == ['a', 'b', 'c']
    clock.advance(1)
    assert lst == ['a', 'b', 'c']
    clock.advance(1)
    assert lst == ['a', 'b', 'c', 'd']

def test_negative_dt():
    clock = Clock()
    with pytest.raises(ValueError):
        clock.advance(-1)
    with pytest.raises(ValueError):
        clock.schedule(dummy_function, -1)

def test_zero_dt():
    clock = Clock()
    lst = []
    clock.schedule(append_const(lst, 'a'), 0)
    clock.advance(0)
    assert lst == ['a']

def test_integer_times():
    """
    Ensure that even if the clock advances by float ticks, events scheduled
    at integer times get fired with clock.time being an integer.
    """
    clock = Clock()
    lst = []
    clock.schedule(append_time(lst, clock), 1)
    clock.schedule(append_time(lst, clock), 2)
    clock.schedule(append_time(lst, clock), 3)
    for i in xrange(30):
        clock.advance(0.3)
    assert lst == [1, 2, 3]
    for time in lst:
        assert type(time) == int
