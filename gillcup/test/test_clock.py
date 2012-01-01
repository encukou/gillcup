from __future__ import division

import pytest

from gillcup import Clock, Subclock

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

def test_update_function():
    time_list = [0]
    clock = Clock()
    def update_function():
        time_list[0] = clock.time
    def do_assert():
        assert time_list[0] == clock.time
    clock.schedule_update_function(update_function)
    do_assert()
    clock.advance(1)
    do_assert()
    clock.schedule(do_assert, 1)
    clock.advance(2)
    do_assert()

def test_recursive_advance():
    clock = Clock()
    clock.schedule(lambda: clock.advance(1))
    with pytest.raises(RuntimeError):
        clock.advance(0)

def test_subclock():
    clock = Clock()
    subclock = Subclock(clock)
    subclock.advance(1)
    assert clock.time == 0
    assert subclock.time == 1
    clock.advance(1)
    assert clock.time == 1
    assert subclock.time == 2
    subclock.speed = 2
    clock.advance(1)
    assert clock.time == 2
    assert subclock.time == 4

    lst = []
    def append_const(lst, c):
        def append():
            print c, clock.time, subclock.time
            lst.append(c)
        return append
    subclock.schedule(append_const(lst, 'a'), 1)
    clock.schedule(append_const(lst, 'b'), 1)
    subclock.schedule(append_const(lst, 'c'), 2)
    clock.advance(1)
    assert lst == ['a', 'b', 'c']
