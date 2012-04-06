"""Tests for the gillcup.clock module"""

from __future__ import unicode_literals, division, print_function

from pytest import raises

from gillcup import Clock, Subclock, Animation


def dummy_function():
    """Helper function; does nothing"""
    pass


def append_const(lst, value):
    """Helper callback; returns func that appends a constant to list"""
    def _append():
        lst.append(value)
    return _append


def append_time(lst, clock):
    """Helper callback; returns func that appends clock's time to list"""
    def _append():
        lst.append(clock.time)
    return _append


def test_clock():
    """Test that simple clock advancement works"""
    clock = Clock()
    assert clock.time == 0
    clock.advance(1)
    assert clock.time == 1


def test_scheduling():
    """Test that simple scheduling works"""
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
    """Test that negative advancements are blocked"""
    clock = Clock()
    with raises(ValueError):
        clock.advance(-1)
    with raises(ValueError):
        clock.schedule(dummy_function, -1)


def test_zero_dt():
    """Test that a zero advancement triggers immediate events"""
    clock = Clock()
    lst = []
    clock.schedule(append_const(lst, 'a'), 0)
    clock.advance(0)
    assert lst == ['a']


def test_integer_times():
    """Test that we keep to int arithmetic as much as we can

    Ensure that even if the clock advances by float ticks, events scheduled
    at integer times get fired with clock.time being an integer.
    """
    clock = Clock()
    lst = []
    clock.schedule(append_time(lst, clock), 1)
    clock.schedule(append_time(lst, clock), 2)
    clock.schedule(append_time(lst, clock), 3)
    for dummy in range(30):
        clock.advance(0.3)
    assert lst == [1, 2, 3]
    for time in lst:
        assert type(time) == int


def test_update_function():
    """Test that schedule_update_function() works"""
    time_list = [0]
    clock = Clock()
    def _update_function():
        time_list[0] = clock.time
    def _do_assert():
        assert time_list[0] == clock.time
    clock.schedule_update_function(_update_function)
    _do_assert()
    clock.advance(1)
    _do_assert()
    clock.schedule(_do_assert, 1)
    clock.advance(2)
    _do_assert()


def test_unschedule_update_function():
    """Test that unschedule_update_function() works"""
    clock = Clock()
    def _update_function():
        raise AssertionError('Update function called!')
    clock.schedule_update_function(_update_function)
    clock.unschedule_update_function(_update_function)
    clock.advance(1)


def test_recursive_advance():
    """Test that calling advance() from within advance() is blocked"""
    clock = Clock()
    clock.schedule(lambda: clock.advance(1))
    with raises(RuntimeError):
        clock.advance(0)


def test_subclock():
    """Test Sublock works"""
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
    def _append_const(lst, value):
        def _append():
            print(value, clock.time, subclock.time)
            lst.append(value)
        return _append
    subclock.schedule(_append_const(lst, 'a'), 1)
    clock.schedule(_append_const(lst, 'b'), 1)
    subclock.schedule(_append_const(lst, 'c'), 2)
    clock.advance(1)
    assert lst == ['a', 'b', 'c']


def test_subclock_speedup():
    """Test Sublock.speed works when set as attribute"""
    clock = Clock()
    subclock = Subclock(clock)
    assert subclock.time == 0
    clock.advance(1)
    assert subclock.time == 1
    subclock.speed = 2
    clock.advance(1)
    assert subclock.time == 3


def test_subclock_speed_arg():
    """Test Sublock.speed works when passed as argument"""
    clock = Clock()
    subclock = Subclock(clock, speed=2)
    assert subclock.time == 0
    clock.advance(1)
    assert subclock.time == 2


def test_subclock_animated_speed():
    """Test behavior is consistent when Sublock.speed is animated"""
    # Slow down time itself -- but only in discrete intervals
    # User shouldn't rely on this. The test is here to catch possible
    # backwards-incompatible behavior (which would need a version bump).
    clock = Clock()
    subclock = Subclock(clock)
    subclock.schedule(Animation(subclock, 'speed', 0, time=2))
    clock.advance(1)
    assert subclock.time == 1
    clock.advance(1)
    assert subclock.time == 1.5
    clock.advance(1)
    assert subclock.time == 1.75
    clock.advance(1)
    assert subclock.time == 1.875
    for dummy in range(1000):
        clock.advance(1)
    assert subclock.time == 2
